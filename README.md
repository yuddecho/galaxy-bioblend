# BioBlend 使用教程整理

## 一、BioBlend 简介

BioBlend 是一个用于与 Galaxy API 交互的 Python 库，旨在简化 Galaxy 分析流程的脚本化和自动化管理。

### 1.1 核心特性
- **双重 API 模式**：提供功能型 API 和面向对象 API 两种编程接口
- **跨平台支持**：支持 Python 3.9-3.14 版本

### 1.2 应用场景
- 自动化生物信息学分析流程
- 批量管理 Galaxy 数据集和工作流
- 云端计算资源动态调配
- 集成到更复杂的分析管道中

---

## 二、安装与配置

### 2.1 安装方法

**推荐方式 - 通过 pip 安装**：

```bash
pip install bioblend
```

**Conda 环境安装**：

```bash
conda create -n bioblend -c bioconda bioblend "python>=3.7"
conda activate bioblend
```

**从源码安装**（获取最新功能）：

```bash
git clone https://github.com/galaxyproject/bioblend.git
cd bioblend
python3 -m pip install .
```

### 2.2 获取 API 密钥

1. 登录 Web 网站
2. 进入 **User → Settings → Manage API key**
3. 生成并复制 API 密钥

---

## 三、基础使用：连接到 Galaxy

```python
from bioblend.galaxy import GalaxyInstance

# 基础连接
gi = GalaxyInstance(url='http://localhost:8080', key='your_api_key')

# 测试连接
try:
    libs = gi.libraries.get_libraries()
    print(f"成功连接，找到 {len(libs)} 个数据文库")
except Exception as e:
    print(f"连接失败: {e}")
```

---

## 四、功能型 API (Functional API) 详解

### 4.1 特点
- 直接的方法调用，简单直观
- 适合快速脚本和一次性任务

### 4.2 核心操作示例

```python
from bioblend.galaxy import GalaxyInstance

gi = GalaxyInstance(url='<Galaxy IP>', key='your_api_key')

# 查询数据文库
libraries = gi.libraries.get_libraries()

# 获取工作流信息
workflow = gi.workflows.show_workflow('workflow_id')

# 运行工作流
wf_invocation = gi.workflows.invoke_workflow(
    'workflow_id',
    inputs={
        '0': {'id': 'dataset_id', 'src': 'hda'},
        '1': {'id': 'dataset_id_2', 'src': 'hda'}
    }
)

# 上传数据集
history_id = 'your_history_id'
gi.tools.upload_file('local_file_path', history_id)

# 查看工作流运行状态
status = gi.invocations.show_invocation(wf_invocation['id'])
```

---

## 五、面向对象 API (Object-Oriented API) 详解

### 5.1 特点
- 更符合 Pythonic 的编程风格
- 对象关系明确，适合复杂项目管理

### 5.2 核心操作示例

```python
from bioblend.galaxy.objects import GalaxyInstance

gi = GalaxyInstance("Galaxy URL", "API_KEY")

# 获取对象
workflow = gi.workflows.list()[0]  # 第一个工作流
history = gi.histories.list()[0]   # 第一个历史记录
datasets = history.get_datasets()[:2]  # 前两个数据集

# 构建输入映射
input_map = dict(zip(workflow.input_labels, datasets))

# 设置参数
params = {"Paste1": {"delimiter": "U"}}

# 运行工作流
wf_invocation = workflow.invoke(input_map, "wf_output", params=params)
```

---

## 六、开发资源

Galaxy API 教学：https://training.galaxyproject.org/training-material/topics/dev/tutorials/bioblend-api/slides.html#1

BioBlend：https://bioblend.readthedocs.io/en/latest/

