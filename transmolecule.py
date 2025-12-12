from bioblend.galaxy import GalaxyInstance

import yaml
import json
import os
import ast

from dataclasses import dataclass


@dataclass
class GalaxyCtx:
    gi: GalaxyInstance
    history_id: str

class History:
    def __init__(self, ctx: GalaxyCtx):
        self.ctx = ctx

    def create(self, name: str = None):
        # 创建一个新的历史记录，并设为当前历史记录
        new_history = self.ctx.gi.histories.create_history(name=name)
        self.ctx.history_id = new_history['id']
        print(f"[History] create {self.ctx.history_id}:{new_history['name']}")

    def select(self, history_id: str):
        # 选择一个历史记录作为当前历史记录
        self.ctx.history_id = history_id
        history_name = self.ctx.gi.histories.show_history(history_id, contents=False)['name']
        print(f"[History] select {self.ctx.history_id}:{history_name}")
    
    def open(self):
        # 打开web, 并选择当前历史记录
        self.ctx.gi.histories.open_history(self.ctx.history_id)

    def delete(self, history_id: str = None, purge=False):
        # 删除历史记录; purge=True时，删除所有相关内容，不可恢复
        # history_id 为 None 时，删除当前历史记录
        if history_id is None:
            # 当前历史记录
            history_id = self.ctx.history_id

            # 将最近历史记录 设为 当前历史记录
            self.ctx.history_id = self.ctx.gi.histories.get_most_recently_used_history()['id']

        self.ctx.gi.histories.delete_history(history_id, purge=purge)

    def info(self):
        # 打印所有历史记录信息
        print("id,\t name,\tcount(items),\t update_time")
        for h in self.ctx.gi.histories.get_histories():
            print(f"{h['id']},\t {h['name']},\t {h['count']},\t {h['update_time']}")

    def content(self, contents=True):
        # 获取历史记录信息; 
        # contents=False （默认值），则只会得到历史记录中包含的数据集的 ID 列表
        # contents=True ，则会得到每个数据集的元数据
        history_id = self.ctx.history_id
        history_info = self.ctx.gi.histories.show_history(history_id, contents=contents)

        if contents:
            if len(history_info) > 0:
                print("id,\t hid,\t deleted,\t name,\t create_time")
                for h in history_info:
                    print(f"{h['id']},\t {h['hid']},\t {h['deleted']},\t {h['name']},\t {h['create_time']}")
            else:
                print(f"No contents in this history: {self.ctx.history_id}")
        else:
            print(json.dumps(history_info, indent=4, ensure_ascii=False))
    
class Dataset:
    def __init__(self, ctx: GalaxyCtx):
        self.ctx = ctx

    def _upload_file(self, file_path: str):
        # 上传文件到当前历史记录
        file_tpye = os.path.splitext(file_path)[1]
        res = self.ctx.gi.tools.upload_file(file_path, self.ctx.history_id, file_tpye=file_tpye)
        return res['outputs'][0]

    def upload(self, file_path: str = None, file_dir: str = None):
        # 上传文件到当前历史记录
        if file_path is None and file_dir is None:
            raise ValueError("file_path or file_dir should be provided")
        
        files = []
        
        if file_path:
            files.append(self._upload_file(file_path))

        if file_dir:
            # 上传目录下所有文件到当前历史记录
            for file_name in os.listdir(file_dir):
                file_path = os.path.join(file_dir, file_name)
                files.append(self._upload_file(file_path))

        data = {}
        for file in files:
            data[file['name']] = file['id']

        return data
    
    def download(self, dataset_id: str, file_path: str):
        # 下载数据集到本地
        self.ctx.gi.datasets.download_dataset(dataset_id, file_path)
    
    def delete(self, dataset_id: str):
        # 删除数据集
        self.ctx.gi.datasets.delete_dataset(dataset_id)
    
    def info(self, dataset_id: str):
        # 获取数据集信息
        dataset_info = self.ctx.gi.datasets.show_dataset(dataset_id)
        return dataset_info
    
    def get(self):
        # 获取当前历史记录中的所有数据集信息
        history_id = self.ctx.history_id
        history_info = self.ctx.gi.histories.show_history(history_id, contents=True)
        data = {}
        if len(history_info) > 0:
            for h in history_info:
                data[h['name']] = h['id']
        return data
    
class BaseTool:
    def __init__(self, ctx: GalaxyCtx, tool_path: str):
        self.ctx = ctx
        with open(tool_path, encoding='utf-8') as f:
            self.tool_config = yaml.safe_load(f)

    def info(self):
        print(json.dumps(self.tool_config, indent=4, ensure_ascii=False))

    def inputs(self):
        return ast.literal_eval(self.tool_config['input_exampels'])
    
    def run(self, inputs: dict) -> dict:    
        # 参数验证
        _inputs = self.inputs()
        if not all(k in inputs for k in _inputs.keys()):
            raise ValueError(f"inputs should contain all keys: {_inputs}")
        
        tool_outputs = self.ctx.gi.tools.run_tool(history_id=self.ctx.history_id, tool_id=self.tool_config['id'], tool_inputs=inputs)

        keep = ['id', 'hid', 'name', 'file_ext']
        outputs = [{k: d[k] for k in keep} for d in tool_outputs['outputs']]

        keep = ['id', 'hid', 'name']
        output_collections = [{k: d[k] for k in keep} for d in tool_outputs['output_collections']]

        keep = ['id', 'state', 'tool_id', 'create_time']
        jobs = [{k: d[k] for k in keep} for d in tool_outputs['jobs']]

        return {'jobs': jobs,'outputs': outputs, 'output_collections': output_collections}

class Tool:
    def __init__(self, ctx: GalaxyCtx):
        self.ctx = ctx
        self.tools = self.ctx.gi.tools.get_tool_panel()
        self.tool_dict = self._get_tool_dict()

    def info(self):
        print('id,\t name,\t description')
        for tool_section in self.tools:
            for tool in tool_section['elems']:
                print(f'{tool["id"]},\t {tool["name"]},\t {tool["description"]}')

    def _get_tool_dict(self):
        tool_dict = {}
        for tool_section in self.tools:
            for tool in tool_section['elems']:
                tool_dict[tool['name']] = tool['id']
        return tool_dict
        
    def get_tool(self, tool_id: str = None, tool_name: str = None) -> BaseTool:
        # tool_id 和 tool_name 至少需要提供一个
        if tool_id is None and tool_name is None:
            raise ValueError("tool_id or tool_name should be provided")
        
        if tool_name:
            _tool_id = self.tool_dict.get(tool_name, None)
            if _tool_id is None:
                raise ValueError(f"tool_name {_tool_id} not found, please check tool name in tool panel: {self.tool_dict}")
            elif tool_id and tool_id != _tool_id:
                raise ValueError(f"tool_name {tool_name} not match tool_id {tool_id}, please check tool name in tool panel: {self.tool_dict}")
            
            tool_id = _tool_id
        
        tool_path = f"tools/{tool_id}.yaml"
        if not os.path.exists(tool_path):
            raise ValueError(f"tool_id {tool_id}.yaml not found, please check tool id in tool panel: {self.tool_dict}")
        
        return BaseTool(self.ctx, tool_path)

class TransMolecule:
    def __init__(self, url, key):
        gi = self.login(url, key)
        history = gi.histories.get_most_recently_used_history()
        print(f"[History] now {history['id']}:{history['name']}")

        self.ctx = GalaxyCtx(gi, history['id'])
        self.history = History(self.ctx)
        self.tool = Tool(self.ctx)
        self.dataset = Dataset(self.ctx)

    def login(self, url, key):
        return GalaxyInstance(url, key)
    

def test():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 登录
    trans_molecule = TransMolecule(config['galaxy_url'], config['api_key'])

    # 创建一个新的历史纪录
    trans_molecule.history.create(name='test_history')

    # 上传数据到当前历史记录
    data = trans_molecule.tool.upload(file_dir='./data/test_1_pharma_pharmapepgen')


if __name__ == '__main__':
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    trans_molecule = TransMolecule(config['galaxy_url'], config['api_key'])

    trans_molecule.history.select('5114a2a207b7caff')

    trans_molecule.history.create(name='test_history1')

    # 获取当前用户所有历史记录信息
    trans_molecule.history.info()

    # 获取当前历史记录数据信息
    trans_molecule.history.content()
    
    # 获取工具信息
    trans_molecule.tool.info()

    # 测试
    # test()
    """
    上一个任务没有完成，会不会等待
    其他工具配置
    """