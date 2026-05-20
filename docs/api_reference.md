# 智能基金监控系统 - API参考文档

> **版本**: v2.0  
> **模块**: 所有公开API  
> **更新日期**: 2026-05-20

---

## 目录

1. [config 模块](#config-模块)
2. [models.database 模块](#modelsdatabase-模块)
3. [services.data_fetcher 模块](#servicesdata_fetcher-模块)
4. [services.notification 模块](#servicesnotification-模块)
5. [ui.widgets 模块](#uiwidgets-模块)
6. [ui.main_window 模块](#uimain_window-模块)

---

## config 模块

### FundConfig

基金监控配置数据类。

**属性**:

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `db_path` | `str` | `'fund_monitor.db'` | 数据库文件路径 |
| `default_refresh_interval` | `int` | `60` | 默认刷新间隔（秒） |
| `min_refresh_interval` | `int` | `5` | 最小刷新间隔（秒） |
| `max_refresh_interval` | `int` | `3600` | 最大刷新间隔（秒） |
| `request_timeout` | `int` | `10` | 网络请求超时时间（秒） |
| `max_retry_times` | `int` | `3` | 最大重试次数 |
| `retry_delay` | `float` | `1.0` | 重试间隔（秒） |
| `fund_api_url` | `str` | `"http://..."` | 基金估值API URL模板 |
| `fund_list_url` | `str` | `"https://..."` | 基金列表API URL |

**使用示例**:

```python
from config import config, FundConfig

# 使用默认配置实例
print(config.default_refresh_interval)  # 60

# 创建自定义配置
custom_config = FundConfig(
    db_path='my_database.db',
    default_refresh_interval=30,
    request_timeout=15
)

# 访问配置
print(custom_config.fund_api_url.format(code="000001"))
```

### 全局实例

```python
config: FundConfig  # 预配置的全局实例
```

---

## models.database 模块

### DatabaseManager

线程安全的数据库管理器，提供所有数据库操作接口。

#### 构造函数

```python
def __init__(self, db_path: str = config.db_path) -> None:
    """初始化数据库管理器
    
    Args:
        db_path: 数据库文件路径，默认使用config中的路径
    """
```

#### 方法

##### get_cursor()

获取数据库游标的上下文管理器。

```python
@contextmanager
def get_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
    """
    Yields:
        sqlite3.Cursor: 数据库游标
        
    Example:
        >>> with db.get_cursor() as cursor:
        ...     cursor.execute('SELECT * FROM monitored_funds')
        ...     results = cursor.fetchall()
        
    Note:
        - 自动提交事务
        - 异常时自动回滚
        - 使用完毕后自动关闭游标
    """
```

##### get_ui_settings()

获取UI偏好设置（眼睛图标状态等）。

```python
def get_ui_settings(self) -> Dict[str, bool]:
    """
    Returns:
        Dict[str, bool]: 包含以下键的字典：
            - profit_visible: 累计盈亏是否可见
            - daily_profit_visible: 今日盈亏是否可见
            - position_cost_visible: 持仓成本是否可见
            - current_value_visible: 持有金额是否可见
            
    Example:
        >>> settings = db.get_ui_settings()
        >>> print(settings['profit_visible'])
        True
    """
```

##### save_ui_setting()

保存单个UI设置项。

```python
def save_ui_setting(self, setting_name: str, value: bool) -> bool:
    """
    Args:
        setting_name: 设置名称，可选值：
            - 'profit_visible'
            - 'daily_profit_visible'
            - 'position_cost_visible'
            - 'current_value_visible'
        value: 可见性状态 (True/False)
        
    Returns:
        bool: 是否保存成功
        
    Raises:
        无显式抛出，失败时记录日志并返回False
        
    Example:
        >>> success = db.save_ui_setting('profit_visible', False)
        >>> print(success)
        True
    """
```

##### close()

关闭数据库连接。

```python
def close(self) -> None:
    """关闭当前线程的数据库连接
    
    Note:
        应在程序退出前调用以释放资源
    """
```

---

## services.data_fetcher 模块

### FundDataFetcher

基金数据获取工具类，提供静态方法访问外部API。

#### 方法（全部为静态方法）

##### get_fund()

获取单只基金的实时估值数据。

```python
@staticmethod
@retry_on_failure(max_retries=config.max_retry_times, 
                  delay=config.retry_delay)
def get_fund(code: str) -> Optional[Dict[str, Any]]:
    """
    获取单个基金数据
    
    Args:
        code: 6位基金代码字符串
        
    Returns:
        Optional[Dict[str, Any]]: 基金数据字典，包含：
            - name (str): 基金名称
            - jzrq (str): 净值日期
            - dwjz (str): 单位净值
            - gsz (str): 估算值
            - gszzl (str): 估算涨跌幅%
            - gztime (str): 估算时间
            
        失败返回None
            
    Example:
        >>> data = FundDataFetcher.get_fund("000001")
        >>> if data:
        ...     print(data['name'], data['gszzl'])
        华夏成长混合 2.35
        
    Raises:
        requests.Timeout: 请求超时（会自动重试）
        requests.RequestException: 网络错误（会自动重试）
        
    Note:
        使用@retry_on_failure装饰器自动重试
    """
```

##### get_all_funds()

获取全市场基金列表（用于搜索功能）。

```python
@staticmethod
@retry_on_failure(max_retries=config.max_retry_times,
                  delay=config.retry_delay)
def get_all_funds() -> Dict[str, Dict[str, str]]:
    """
    获取所有基金列表
    
    Returns:
        Dict[str, Dict[str, str]]: 字典格式：
            {
                "000001": {
                    "name": "华夏成长混合",
                    "pinyin": "hxcczh"
                },
                ...
            }
            
    Example:
        >>> funds = FundDataFetcher.get_all_funds()
        >>> print(f"共{len(funds)}只基金")
        共8000+只基金
        
        >>> # 搜索示例
        >>> results = {k: v for k, v in funds.items() 
        ...           if "华夏" in v['name']}
    """
```

##### validate_fund_code()

验证基金代码格式是否正确。

```python
@staticmethod
def validate_fund_code(code: str) -> Tuple[bool, str]:
    """
    验证基金代码有效性
    
    Args:
        code: 待验证的基金代码字符串
        
    Returns:
        Tuple[bool, str]: (是否有效, 错误消息)
            - 有效时返回 (True, "")
            - 无效时返回 (False, "错误原因")
            
    Example:
        >>> FundDataFetcher.validate_fund_code("000001")
        (True, '')
        
        >>> FundDataFetcher.validate_fund_code("abc")
        (False, '基金代码必须为数字')
        
        >>> FundDataFetcher.validate_fund_code("12345")
        (False, '基金代码必须为6位数字')
    """
```

---

## services.notification 模块

### NotificationManager

多渠道通知管理器，支持弹窗和钉钉通知。

#### 构造函数

```python
def __init__(self, db_manager: DatabaseManager) -> None:
    """
    Args:
        db_manager: 数据库管理器实例（用于读取通知设置）
    """
```

#### 方法

##### get_notification_settings()

获取通知配置。

```python
def get_notification_settings(self) -> Dict[str, Any]:
    """
    Returns:
        Dict[str, Any]: 通知设置字典，包含：
            - popup_enabled (bool): 是否启用弹窗通知
            - dingtalk_enabled (bool): 是否启用钉钉通知
            - dingtalk_webhook (str): 钉钉Webhook地址
            - rise_threshold (float): 涨幅预警阈值（%）
            - fall_threshold (float): 跌幅预警阈值（%）
            - profit_threshold (float): 盈利预警阈值（元）
            - loss_threshold (float): 亏损预警阈值（元）
            ...其他邮箱相关设置
    """
```

##### send_popup_notification()

发送系统弹窗通知。

```python
def send_popup_notification(self, title: str, message: str) -> None:
    """
    发送系统托盘弹窗通知
    
    Args:
        title: 通知标题
        message: 通知内容
        
    Note:
        - 受popup_enabled开关控制
        - 有5分钟冷却时间（同类型通知）
    """
```

##### send_dingtalk_notification()

发送钉钉机器人通知。

```python
def send_dingtalk_notification(self, title: str, message: str) -> None:
    """
    发送钉钉群机器人通知
    
    Args:
        title: 通知标题（Markdown格式）
        message: 通知内容（支持Markdown）
        
    Note:
        - 需要预先配置dingtalk_webhook
        - 有5分钟冷却时间
        - 使用Markdown格式化消息
    """
```

##### check_and_notify()

根据阈值自动检查并发送通知。

```python
def check_and_notify(
    self, 
    fund_data: Dict[str, Dict], 
    total_profit: float, 
    daily_profit: float
) -> None:
    """
    检查各项指标并触发通知
    
    Args:
        fund_data: 基金数据字典 {code: fund_info}
        total_profit: 累计盈亏金额
        daily_profit: 当日盈亏金额
        
    触发条件：
        - 单只基金涨幅 >= rise_threshold
        - 单只基金跌幅 <= fall_threshold
        - 累计盈利 >= profit_threshold
        - 累计亏损 <= loss_threshold
    """
```

---

## ui.widgets 模块

### FundTableWidget

自定义的基金数据表格组件，继承自QTableWidget。

#### 构造函数

```python
def __init__(self, parent_monitor: Optional[FundMonitor] = None) -> None:
    """
    Args:
        parent_monitor: 父级FundMonitor窗口引用，
                      用于回调操作（如更新总盈亏）
    """
```

#### 方法

##### setup_ui()

初始化表格UI和样式。

```python
def setup_ui(self) -> None:
    """
    设置表格属性：
    - 14列数据展示
    - 启用排序
    - 禁用编辑
    - 右键菜单
    - 现代化样式
    """
```

##### update_data()

更新表格数据。

```python
def update_data(self, fund_data: Dict[str, Dict]) -> None:
    """
    更新表格显示的数据
    
    Args:
        fund_data: 基金数据字典 {code: fund_data_dict}
        
    功能：
        - 清空并重新填充表格
        - 计算盈亏数据
        - 应用颜色编码（红涨绿跌）
        - 调用父窗口更新总计数据
        
    Example:
        >>> data = {"000001": {'name': '...', 'gszzl': '2.35', ...}}
        >>> table.update_data(data)
    """
```

##### show_context_menu(position)

显示右键上下文菜单。

```python
@Slot(QPoint)
def show_context_menu(self, position: QPoint) -> None:
    """
    显示右键菜单
    
    菜单项（针对已监控基金）：
    - 删除基金监控
    - 设置持仓成本价
    - 设置持有份额
    - 记录分红
    
    菜单项（空白区域）：
    - 添加新基金
    - 显示/隐藏列（子菜单）
    """
```

##### toggle_column_visibility()

切换指定列的显示/隐藏状态。

```python
def toggle_column_visibility(self, column: int) -> None:
    """
    切换列可见性
    
    Args:
        column: 列索引（0-based）
    """
```

### PercentageItem

用于百分比数据排序的表格项类。

```python
class PercentageItem(QTableWidgetItem):
    """支持百分比格式排序的表格项"""
    
    def __lt__(self, other: QTableWidgetItem) -> bool:
        """
        比较逻辑：去除%符号后比较数值
        
        Example:
        >>> item1 = PercentageItem("2.35%")
        >>> item2 = PercentageItem("1.50%")
        >>> item1 < item2  # False, 因为 2.35 > 1.50
        """
```

### NumericItem

用于数值排序的表格项类。

```python
class NumericItem(QTableWidgetItem):
    """支持数值排序的表格项"""
    
    def __lt__(self, other: QTableWidgetItem) -> bool:
        """
        比较逻辑：转换为float后比较
        
        Example:
        >>> item1 = NumericItem("1500.00")
        >>> item2 = NumericItem("800.50")
        >>> item1 < item2  # False
        """
```

### FundSearchWidget

基金搜索组件，提供搜索和添加功能。

#### 信号

```python
fund_selected: Signal(str)  # 当用户选中基金并发送时触发
```

#### 方法

##### filter_funds(text)

过滤基金列表。

```python
@Slot(str)
def filter_funds(self, text: str) -> None:
    """
    根据输入文本过滤基金列表
    
    Args:
        text: 搜索关键词（匹配代码或名称）
    """
```

---

## ui.main_window 模块

### FundMonitor

主应用程序窗口，继承自QMainWindow。

#### 构造函数与初始化

```python
def __init__(self) -> None:
    """
    初始化主窗口：
    1. 设置窗口属性（标题、大小、图标）
    2. 初始化数据库和通知管理器
    3. 加载监控基金列表
    4. 从数据库恢复UI设置
    5. 创建界面组件
    6. 启动定时器和数据刷新
    """
```

#### 核心业务方法

##### add_fund_to_monitor(code)

添加基金到监控列表。

```python
def add_fund_to_monitor(self, fund_code: str) -> bool:
    """
    添加基金到监控列表
    
    Args:
        fund_code: 6位基金代码
        
    Returns:
        bool: 是否添加成功
        
    流程：
        1. 验证基金代码格式
        2. 检查是否已存在
        3. 从API获取基金信息
        4. 写入数据库
        5. 刷新数据显示
    """
```

##### remove_specific_fund(code)

从监控列表删除基金。

```python
def remove_specific_fund(self, fund_code: str) -> bool:
    """
    删除指定基金及其持仓数据
    
    Args:
        fund_code: 要删除的基金代码
        
    Note:
        至少保留一只基金
    """
```

##### update_fund_holdings_detail()

更新基金的持仓详情。

```python
def update_fund_holdings_detail(
    self,
    fund_code: str,
    cost_price: Optional[float] = None,
    shares: Optional[float] = None,
    amount: Optional[float] = None
) -> bool:
    """
    更新基金持仓信息（支持部分更新）
    
    Args:
        fund_code: 基金代码
        cost_price: 持仓成本价（可选）
        shares: 持有份额（可选）
        amount: 持有金额（可选）
        
    Returns:
        bool: 是否更新成功
        
    Example:
        >>> success = monitor.update_fund_holdings_detail(
        ...     "000001",
        ...     cost_price=1.5,
        ...     shares=1000.0
        ... )
    """
```

##### toggle_stat_visibility()

切换统计数据的显示/隐藏。

```python
def toggle_stat_visibility(
    self,
    stat_name: str,
    value_label: QLabel,
    eye_btn: QPushButton
) -> None:
    """
    切换统计数据可见性
    
    Args:
        stat_name: 统计项名称 ("今日盈亏"/"持仓成本"/"持有金额")
        value_label: 数值标签控件
        eye_btn: 眼睛图标按钮
        
    功能：
        - 切换显示/隐藏状态
        - 保存状态到数据库（持久化）
        - 更新按钮图标（👁/🔒）
    """
```

##### toggle_profit_visibility()

切换累计盈亏的显示/隐藏。

```python
def toggle_profit_visibility(self) -> None:
    """切换累计盈亏可见性（带持久化）"""
```

##### get_fund_holdings_detail()

获取基金的详细持仓信息。

```python
def get_fund_holdings_detail(
    self, fund_code: str
) -> Tuple[float, float, float]:
    """
    获取基金持仓详情
    
    Args:
        fund_code: 基金代码
        
    Returns:
        Tuple[float, float, float]: (成本价, 份额, 金额)
        
    Example:
        >>> cost, shares, amount = monitor.get_fund_holdings_detail("000001")
        >>> print(f"成本:{cost}, 份额:{shares}, 金额:{amount}")
    """
```

##### get_fund_dividend()

获取基金的分红总额。

```python
def get_fund_dividend(self, fund_code: str) -> float:
    """
    获取某只基金的累计分红金额
    
    Args:
        fund_code: 基金代码
        
    Returns:
        float: 分红总额（元），无分红返回0.0
    """
```

##### record_dividend()

记录基金分红。

```python
def record_dividend(self, fund_code: str) -> None:
    """
    弹出对话框记录分红金额
    
    Args:
        fund_code: 基金代码
        
    流程：
        1. 显示输入对话框
        2. 用户输入金额
        3. 写入dividend_records表
        4. 刷新数据
    """
```

##### update_total_profit()

更新总盈亏显示。

```python
def update_total_profit(
    self,
    profit: float,
    daily_profit: float = 0.0,
    position_cost: float = 0.0,
    current_value: float = 0.0
) -> None:
    """
    更新顶部统计栏的总盈亏数据
    
    Args:
        profit: 累计盈亏金额
        daily_profit: 当日盈亏金额
        position_cost: 总持仓成本
        current_value: 总持有金额
        
    功能：
        - 更新累计盈亏标签（含颜色）
        - 更新今日盈亏标签
        - 更新持仓成本标签
        - 更新持有金额标签
        - 尊重用户的隐藏设置
    """
```

#### 对话框类

##### AddFundDialog

添加基金对话框。

```python
class AddFundDialog(QDialog):
    """基金代码输入对话框"""
    
    def get_code(self) -> str:
        """返回用户输入的基金代码"""
```

##### NotificationSettingsDialog

通知设置对话框。

```python
class NotificationSettingsDialog(QDialog):
    """通知配置对话框"""
    
    def load_settings(self) -> None:
        """从数据库加载当前设置"""
        
    def save_settings(self) -> None:
        """保存用户修改的设置"""
```

##### FundHistoryChartWindow

历史净值图表窗口。

```python
class FundHistoryChartWindow(QDialog):
    """基金净值走势图窗口"""
    
    def __init__(self, fund_code: str, parent=None):
        """
        Args:
            fund_code: 要查看的基金代码
        """
```

---

## 工具函数

### utils.decorators 模块

##### retry_on_failure()

重试装饰器。

```python
def retry_on_failure(
    max_retries: int = 3, 
    delay: float = 1.0
) -> Callable[[F], F]:
    """
    失败自动重试装饰器
    
    Args:
        max_retries: 最大重试次数
        delay: 重试间隔（秒）
        
    Example:
        >>> @retry_on_failure(max_retries=5, delay=2.0)
        ... def unstable_operation():
        ...     pass
    """
```

##### measure_time()

执行时间测量装饰器。

```python
def measure_time(func: F) -> F:
    """
    测量并记录函数执行时间
    
    Example:
        >>> @measure_time
        ... def slow_function():
        ...     time.sleep(1)
        # 日志输出: slow_function 执行时间: 1.xxx秒
    """
```

### utils.logger 模块

##### setup_logger()

创建配置好的日志记录器。

```python
def setup_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO
) -> logging.Logger:
    """
    配置日志记录器
    
    Args:
        name: 记录器名称
        log_file: 日志文件路径
        level: 日志级别
        
    Returns:
        logging.Logger: 配置好的记录器
        
    特性：
        - 同时输出到文件和控制台
        - 文件自动轮转（10MB上限，保留5个备份）
        - 统一的时间戳格式
    """
```

---

## 异常类

本项目未定义自定义异常类，使用Python内置异常：

- `ValueError`: 参数验证失败
- `requests.RequestException`: 网络请求错误
- `sqlite3.DatabaseError`: 数据库操作错误

---

## 类型定义

### 常用类型别名

```python
from typing import Any, Dict, List, Optional, Tuple, Callable, Generator

# 基金数据字典
FundData = Dict[str, Any]
# 示例: {'name': '...', 'gszzl': '2.35', ...}

# 基金列表
FundList = Dict[str, Dict[str, str]]
# 示例: {'000001': {'name': '...', 'pinyin': '...'}, ...}

# UI设置字典
UISettings = Dict[str, bool]
# 示例: {'profit_visible': True, ...}
```

---

## 版本信息

- **当前版本**: v2.0.0
- **API稳定性**: Beta（可能在未来版本调整）
- **向后兼容**: 保证 minor 版本内兼容

---

**📚 文档结束**

更多使用示例请参考测试文件：`tests/test_*.py`
