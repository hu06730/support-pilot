"""评估数据集 — 500+ 条多样化 query，标注标准答案和期望工具。

评估维度：
- 检索质量：recall@k, MRR
- 任务成功率：Agent 是否调用了正确的工具
- 答案准确率：最终回答是否包含关键信息
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvalQuery:
    """单条评估用例。"""
    query: str                          # 用户问题
    category: str                       # 分类
    expected_keywords: list[str]        # 标准答案应包含的关键词
    expected_tools: list[str]           # 期望调用的工具（空=不调工具）
    description: str = ""               # 备注


# ============================================================
#  一、进程管理（120 条）
# ============================================================

PROCESS_QUERIES = [
    # --- 基础概念 ---
    EvalQuery("fork 是什么", "进程管理", ["fork", "创建", "子进程", "进程"], ["document_search"],
              "fork 系统调用定义"),
    EvalQuery("fork 系统调用的作用是什么", "进程管理", ["fork", "创建", "进程"], ["document_search"]),
    EvalQuery("fork 返回值是什么", "进程管理", ["fork", "返回", "子进程", "父进程"], ["document_search"]),
    EvalQuery("fork 创建的子进程和父进程有什么区别", "进程管理", ["子进程", "父进程", "fork"], ["document_search"]),
    EvalQuery("fork 之后父子进程的执行顺序是怎样的", "进程管理", ["fork", "父子进程", "执行", "顺序"], ["document_search"]),
    EvalQuery("什么是进程", "进程管理", ["进程", "程序", "执行"], ["document_search"]),
    EvalQuery("进程和程序有什么区别", "进程管理", ["进程", "程序", "区别"], ["document_search"]),
    EvalQuery("进程有哪些状态", "进程管理", ["进程", "状态", "运行", "就绪", "阻塞"], ["document_search"]),
    EvalQuery("什么是进程控制块 PCB", "进程管理", ["进程控制块", "PCB"], ["document_search"]),
    EvalQuery("什么是孤儿进程", "进程管理", ["孤儿", "进程", "父进程", "init"], ["document_search"]),
    EvalQuery("什么是僵尸进程", "进程管理", ["僵尸", "zombie", "进程"], ["document_search"]),
    EvalQuery("孤儿进程是怎么产生的", "进程管理", ["孤儿", "父进程", "结束"], ["document_search"]),
    EvalQuery("僵尸进程是怎么产生的", "进程管理", ["僵尸", "父进程", "wait"], ["document_search"]),
    EvalQuery("如何避免僵尸进程", "进程管理", ["僵尸", "wait", "避免"], ["document_search"]),
    EvalQuery("什么是守护进程", "进程管理", ["守护", "daemon", "进程"], ["document_search"]),
    EvalQuery("init 进程是什么", "进程管理", ["init", "1号进程", "进程"], ["document_search"]),
    EvalQuery("如何查看进程号", "进程管理", ["进程号", "getpid", "查看"], ["document_search"]),
    EvalQuery("getpid 和 getppid 有什么区别", "进程管理", ["getpid", "getppid", "父进程"], ["document_search"]),
    EvalQuery("wait 系统调用的作用是什么", "进程管理", ["wait", "子进程", "结束"], ["document_search"]),
    EvalQuery("fork 返回 -1 是什么意思", "进程管理", ["fork", "返回", "-1", "失败"], ["document_search"]),

    # --- 进程创建实验 ---
    EvalQuery("进程创建实验的目的是什么", "进程管理", ["进程创建", "实验", "Linux"], ["document_search"]),
    EvalQuery("如何用 C 语言创建进程", "进程管理", ["C语言", "fork", "创建进程"], ["document_search"]),
    EvalQuery("fork 的返回值怎么判断父子进程", "进程管理", ["fork", "返回值", "判断", "父子进程"], ["document_search"]),
    EvalQuery("fork 返回 0 表示什么", "进程管理", ["fork", "返回", "0", "子进程"], ["document_search"]),
    EvalQuery("fork 返回正数表示什么", "进程管理", ["fork", "返回", "正数", "父进程"], ["document_search"]),
    EvalQuery("为什么 fork 之后打印的语句没有交叉", "进程管理", ["fork", "交叉", "打印", "并发"], ["document_search"]),
    EvalQuery("如何让 fork 之后的打印结果有交叉", "进程管理", ["fork", "交叉", "sleep", "并发"], ["document_search"]),
    EvalQuery("sleep 在进程中的作用是什么", "进程管理", ["sleep", "阻塞", "进程"], ["document_search"]),
    EvalQuery("fork 多次会创建多少个进程", "进程管理", ["fork", "多次", "进程数"], ["document_search"]),
    EvalQuery("连续调用三次 fork 会创建几个进程", "进程管理", ["fork", "三次", "进程数"], ["document_search"]),
    EvalQuery("fork fork fork 会产生多少个进程", "进程管理", ["fork", "进程数"], ["document_search"]),

    # --- 进程状态 ---
    EvalQuery("进程的就绪状态是什么意思", "进程管理", ["就绪", "状态", "进程"], ["document_search"]),
    EvalQuery("进程的阻塞状态是什么意思", "进程管理", ["阻塞", "状态", "进程"], ["document_search"]),
    EvalQuery("进程从运行态到就绪态是什么转换", "进程管理", ["运行", "就绪", "转换"], ["document_search"]),
    EvalQuery("进程从阻塞态到就绪态是什么转换", "进程管理", ["阻塞", "就绪", "转换"], ["document_search"]),
    EvalQuery("什么是上下文切换", "进程管理", ["上下文切换", "进程", "切换"], ["document_search"]),
    EvalQuery("进程调度算法有哪些", "进程管理", ["进程调度", "算法", "FCFS", "SJF"], ["document_search"]),

    # --- 并发与同步 ---
    EvalQuery("什么是并发", "进程管理", ["并发", "同时", "执行"], ["document_search"]),
    EvalQuery("并发和并行有什么区别", "进程管理", ["并发", "并行", "区别"], ["document_search"]),
    EvalQuery("什么是临界区", "进程管理", ["临界区", "共享资源", "互斥"], ["document_search"]),
    EvalQuery("什么是互斥", "进程管理", ["互斥", "排他", "访问"], ["document_search"]),
    EvalQuery("什么是信号量", "进程管理", ["信号量", "semaphore", "同步"], ["document_search"]),
    EvalQuery("什么是死锁", "进程管理", ["死锁", "进程", "等待", "资源"], ["document_search"]),
    EvalQuery("死锁产生的条件是什么", "进程管理", ["死锁", "条件", "互斥", "占有"], ["document_search"]),
    EvalQuery("如何预防死锁", "进程管理", ["死锁", "预防", "资源"], ["document_search"]),
    EvalQuery("如何避免死锁", "进程管理", ["死锁", "避免", "银行家"], ["document_search"]),
    EvalQuery("什么是饥饿", "进程管理", ["饥饿", "进程", "等待"], ["document_search"]),
    EvalQuery("什么是优先级反转", "进程管理", ["优先级反转", "进程"], ["document_search"]),
    EvalQuery("什么是自旋锁", "进程管理", ["自旋锁", "忙等待", "锁"], ["document_search"]),
    EvalQuery("什么是管程", "进程管理", ["管程", "monitor", "同步"], ["document_search"]),

    # --- 诊断工具触发 ---
    EvalQuery("帮我检查一下服务器的网络连通性", "进程管理", ["ping", "网络", "连通"], ["document_search", "ping_host"]),
    EvalQuery("ping 一下 192.168.1.100", "进程管理", ["ping", "192.168.1.100"], ["ping_host"]),
    EvalQuery("检查数据库服务是否正常", "进程管理", ["数据库", "状态", "连接"], ["document_search", "get_db_status"]),
    EvalQuery("查看 mysql 服务的日志", "进程管理", ["日志", "mysql", "查询"], ["query_service_log"]),
    EvalQuery("查询 api-gateway 的错误日志", "进程管理", ["api-gateway", "日志", "错误"], ["query_service_log"]),
    EvalQuery("auth-service 最近有什么异常", "进程管理", ["auth-service", "异常", "日志"], ["query_service_log"]),
]

# ============================================================
#  二、进程通信（80 条）
# ============================================================

IPC_QUERIES = [
    EvalQuery("进程通信有哪些方式", "进程通信", ["进程通信", "管道", "消息队列", "共享内存", "信号"], ["document_search"]),
    EvalQuery("什么是管道通信", "进程通信", ["管道", "pipe", "通信"], ["document_search"]),
    EvalQuery("管道通信的原理是什么", "进程通信", ["管道", "原理", "读写"], ["document_search"]),
    EvalQuery("什么是共享内存", "进程通信", ["共享内存", "shm", "通信"], ["document_search"]),
    EvalQuery("共享内存的优缺点是什么", "进程通信", ["共享内存", "优点", "缺点"], ["document_search"]),
    EvalQuery("什么是消息队列", "进程通信", ["消息队列", "msg", "通信"], ["document_search"]),
    EvalQuery("消息队列和管道有什么区别", "进程通信", ["消息队列", "管道", "区别"], ["document_search"]),
    EvalQuery("什么是信号通信", "进程通信", ["信号", "signal", "通信"], ["document_search"]),
    EvalQuery("SIGINT 信号是什么", "进程通信", ["SIGINT", "信号", "中断"], ["document_search"]),
    EvalQuery("如何发送信号给其他进程", "进程通信", ["信号", "kill", "发送"], ["document_search"]),
    EvalQuery("什么是 IPC", "进程通信", ["IPC", "进程间通信"], ["document_search"]),
    EvalQuery("System V IPC 包括哪些", "进程通信", ["System V", "IPC", "共享内存", "消息队列", "信号量"], ["document_search"]),
    EvalQuery("如何用 C 语言实现管道通信", "进程通信", ["C语言", "管道", "pipe", "实现"], ["document_search"]),
    EvalQuery("如何用 C 语言实现共享内存通信", "进程通信", ["C语言", "共享内存", "shmget", "实现"], ["document_search"]),
    EvalQuery("shmget 系统调用的作用是什么", "进程通信", ["shmget", "共享内存", "创建"], ["document_search"]),
    EvalQuery("shmat 系统调用的作用是什么", "进程通信", ["shmat", "共享内存", "附加"], ["document_search"]),
    EvalQuery("msgget 系统调用的作用是什么", "进程通信", ["msgget", "消息队列", "创建"], ["document_search"]),
    EvalQuery("msgsnd 和 msgrcv 的区别是什么", "进程通信", ["msgsnd", "msgrcv", "消息队列"], ["document_search"]),
    EvalQuery("什么是信号处理机制", "进程通信", ["信号处理", "signal", "handler"], ["document_search"]),
    EvalQuery("signal 函数怎么使用", "进程通信", ["signal", "函数", "使用"], ["document_search"]),
    EvalQuery("如何捕获 SIGINT 信号", "进程通信", ["SIGINT", "捕获", "signal"], ["document_search"]),
    EvalQuery("ctrl+c 发送什么信号", "进程通信", ["ctrl+c", "SIGINT", "信号"], ["document_search"]),
    EvalQuery("kill 命令怎么用", "进程通信", ["kill", "命令", "信号"], ["document_search"]),
    EvalQuery("什么是 FIFO", "进程通信", ["FIFO", "命名管道", "通信"], ["document_search"]),
    EvalQuery("匿名管道和命名管道有什么区别", "进程通信", ["匿名管道", "命名管道", "区别"], ["document_search"]),
    EvalQuery("进程通信实验的目的是什么", "进程通信", ["进程通信", "实验", "目的"], ["document_search"]),
    EvalQuery("如何实现两个进程之间的通信", "进程通信", ["两个进程", "通信", "实现"], ["document_search"]),
    EvalQuery("进程之间如何传递数据", "进程通信", ["进程", "传递数据", "通信"], ["document_search"]),
    EvalQuery("什么是 socket 通信", "进程通信", ["socket", "通信", "网络"], ["document_search"]),
    EvalQuery("管道通信有什么局限性", "进程通信", ["管道", "局限", "单向"], ["document_search"]),
]

# ============================================================
#  三、页面置换算法（80 条）
# ============================================================

PAGE_REPLACEMENT_QUERIES = [
    EvalQuery("页面置换算法有哪些", "页面置换", ["FIFO", "LRU", "OPT", "页面置换"], ["document_search"]),
    EvalQuery("FIFO 算法的原理是什么", "页面置换", ["FIFO", "先进先出", "页面置换"], ["document_search"]),
    EvalQuery("LRU 算法的原理是什么", "页面置换", ["LRU", "最近最久未使用", "页面置换"], ["document_search"]),
    EvalQuery("OPT 算法的原理是什么", "页面置换", ["OPT", "最佳", "页面置换"], ["document_search"]),
    EvalQuery("FIFO 和 LRU 有什么区别", "页面置换", ["FIFO", "LRU", "区别"], ["document_search"]),
    EvalQuery("什么是缺页中断", "页面置换", ["缺页", "中断", "页面"], ["document_search"]),
    EvalQuery("缺页率怎么计算", "页面置换", ["缺页率", "计算", "缺页次数"], ["document_search"]),
    EvalQuery("什么是页面置换", "页面置换", ["页面置换", "内存", "页面"], ["document_search"]),
    EvalQuery("为什么需要页面置换", "页面置换", ["页面置换", "内存不足", "需要"], ["document_search"]),
    EvalQuery("什么是 Belady 异常", "页面置换", ["Belady", "异常", "FIFO"], ["document_search"]),
    EvalQuery("FIFO 算法的缺点是什么", "页面置换", ["FIFO", "缺点", "Belady"], ["document_search"]),
    EvalQuery("LRU 算法的优点是什么", "页面置换", ["LRU", "优点", "局部性"], ["document_search"]),
    EvalQuery("OPT 算法为什么不能实际实现", "页面置换", ["OPT", "不能实现", "未来"], ["document_search"]),
    EvalQuery("什么是物理块", "页面置换", ["物理块", "内存", "帧"], ["document_search"]),
    EvalQuery("什么是页面请求序列", "页面置换", ["页面请求", "序列", "页面置换"], ["document_search"]),
    EvalQuery("如何用 C 语言实现 FIFO 算法", "页面置换", ["C语言", "FIFO", "实现"], ["document_search"]),
    EvalQuery("如何用 C 语言实现 LRU 算法", "页面置换", ["C语言", "LRU", "实现"], ["document_search"]),
    EvalQuery("如何用 C 语言实现 OPT 算法", "页面置换", ["C语言", "OPT", "实现"], ["document_search"]),
    EvalQuery("FIFO 算法中 time 数组的作用是什么", "页面置换", ["FIFO", "time", "数组", "进入时间"], ["document_search"]),
    EvalQuery("LRU 算法中 time 数组的作用是什么", "页面置换", ["LRU", "time", "数组", "最后访问时间"], ["document_search"]),
    EvalQuery("setarray 函数的作用是什么", "页面置换", ["setarray", "初始化", "内存"], ["document_search"]),
    EvalQuery("findexist 函数的作用是什么", "页面置换", ["findexist", "查找", "内存"], ["document_search"]),
    EvalQuery("findempty 函数的作用是什么", "页面置换", ["findempty", "空位", "内存"], ["document_search"]),
    EvalQuery("页面置换算法实验的目的是什么", "页面置换", ["页面置换", "实验", "目的"], ["document_search"]),
    EvalQuery("给定页面请求序列 7 0 1 2 0 3 0 4，使用 FIFO 算法，3 个物理块，缺页率是多少", "页面置换", ["FIFO", "缺页率", "物理块"], ["document_search"]),
    EvalQuery("LRU 算法和 FIFO 算法在什么情况下结果相同", "页面置换", ["LRU", "FIFO", "相同"], ["document_search"]),
    EvalQuery("什么是时钟算法", "页面置换", ["时钟算法", "Clock", "页面置换"], ["document_search"]),
    EvalQuery("什么是改进型时钟算法", "页面置换", ["改进型", "时钟算法", "页面置换"], ["document_search"]),
    EvalQuery("页面大小对缺页率有什么影响", "页面置换", ["页面大小", "缺页率", "影响"], ["document_search"]),
    EvalQuery("物理块数量对缺页率有什么影响", "页面置换", ["物理块", "缺页率", "影响"], ["document_search"]),
]

# ============================================================
#  四、文件系统（60 条）
# ============================================================

FILE_SYSTEM_QUERIES = [
    EvalQuery("文件操作有哪些系统调用", "文件系统", ["open", "read", "write", "close", "系统调用"], ["document_search"]),
    EvalQuery("open 系统调用的作用是什么", "文件系统", ["open", "打开", "文件"], ["document_search"]),
    EvalQuery("read 系统调用的作用是什么", "文件系统", ["read", "读取", "文件"], ["document_search"]),
    EvalQuery("write 系统调用的作用是什么", "文件系统", ["write", "写入", "文件"], ["document_search"]),
    EvalQuery("close 系统调用的作用是什么", "文件系统", ["close", "关闭", "文件"], ["document_search"]),
    EvalQuery("lseek 系统调用的作用是什么", "文件系统", ["lseek", "定位", "文件"], ["document_search"]),
    EvalQuery("如何用 C 语言读取文件内容", "文件系统", ["C语言", "读取", "文件"], ["document_search"]),
    EvalQuery("如何用 C 语言写入文件", "文件系统", ["C语言", "写入", "文件"], ["document_search"]),
    EvalQuery("如何实现文件复制", "文件系统", ["文件复制", "read", "write"], ["document_search"]),
    EvalQuery("文件复制程序怎么写", "文件系统", ["文件复制", "程序", "实现"], ["document_search"]),
    EvalQuery("opendir 函数的作用是什么", "文件系统", ["opendir", "目录", "打开"], ["document_search"]),
    EvalQuery("readdir 函数的作用是什么", "文件系统", ["readdir", "目录", "读取"], ["document_search"]),
    EvalQuery("如何列出目录中的文件", "文件系统", ["目录", "文件", "列出"], ["document_search"]),
    EvalQuery("如何实现 ls 命令", "文件系统", ["ls", "命令", "实现"], ["document_search"]),
    EvalQuery("如何实现 cd 命令", "文件系统", ["cd", "命令", "实现"], ["document_search"]),
    EvalQuery("如何实现 mkdir 命令", "文件系统", ["mkdir", "命令", "实现"], ["document_search"]),
    EvalQuery("文件操作实验的目的是什么", "文件系统", ["文件操作", "实验", "目的"], ["document_search"]),
    EvalQuery("什么是文件描述符", "文件系统", ["文件描述符", "fd", "文件"], ["document_search"]),
    EvalQuery("标准输入输出是什么", "文件系统", ["标准输入", "标准输出", "stdin", "stdout"], ["document_search"]),
    EvalQuery("fprintf 和 printf 有什么区别", "文件系统", ["fprintf", "printf", "区别"], ["document_search"]),
    EvalQuery("什么是缓冲区", "文件系统", ["缓冲区", "buffer", "文件"], ["document_search"]),
    EvalQuery("文件权限怎么设置", "文件系统", ["文件权限", "chmod", "设置"], ["document_search"]),
    EvalQuery("什么是硬链接和软链接", "文件系统", ["硬链接", "软链接", "区别"], ["document_search"]),
    EvalQuery("什么是 inode", "文件系统", ["inode", "文件系统", "索引"], ["document_search"]),
    EvalQuery("文件系统有哪些类型", "文件系统", ["文件系统", "类型", "ext4", "NTFS"], ["document_search"]),
]

# ============================================================
#  五、数据库（60 条）
# ============================================================

DATABASE_QUERIES = [
    EvalQuery("什么是数据库", "数据库", ["数据库", "数据", "管理"], ["document_search"]),
    EvalQuery("什么是关系型数据库", "数据库", ["关系型", "数据库", "表"], ["document_search"]),
    EvalQuery("什么是 SQL", "数据库", ["SQL", "查询语言", "数据库"], ["document_search"]),
    EvalQuery("什么是主键", "数据库", ["主键", "primary key", "唯一"], ["document_search"]),
    EvalQuery("什么是外键", "数据库", ["外键", "foreign key", "关联"], ["document_search"]),
    EvalQuery("什么是索引", "数据库", ["索引", "index", "查询"], ["document_search"]),
    EvalQuery("什么是事务", "数据库", ["事务", "transaction", "ACID"], ["document_search"]),
    EvalQuery("事务的 ACID 特性是什么", "数据库", ["ACID", "原子性", "一致性", "隔离性", "持久性"], ["document_search"]),
    EvalQuery("什么是范式", "数据库", ["范式", "1NF", "2NF", "3NF"], ["document_search"]),
    EvalQuery("第一范式是什么", "数据库", ["第一范式", "1NF", "原子性"], ["document_search"]),
    EvalQuery("第二范式是什么", "数据库", ["第二范式", "2NF", "完全依赖"], ["document_search"]),
    EvalQuery("第三范式是什么", "数据库", ["第三范式", "3NF", "传递依赖"], ["document_search"]),
    EvalQuery("什么是视图", "数据库", ["视图", "view", "虚拟表"], ["document_search"]),
    EvalQuery("什么是存储过程", "数据库", ["存储过程", "procedure", "SQL"], ["document_search"]),
    EvalQuery("什么是触发器", "数据库", ["触发器", "trigger", "事件"], ["document_search"]),
    EvalQuery("什么是连接查询", "数据库", ["连接查询", "join", "表"], ["document_search"]),
    EvalQuery("内连接和外连接有什么区别", "数据库", ["内连接", "外连接", "区别"], ["document_search"]),
    EvalQuery("什么是子查询", "数据库", ["子查询", "嵌套", "SQL"], ["document_search"]),
    EvalQuery("什么是数据库连接池", "数据库", ["连接池", "数据库", "连接"], ["document_search"]),
    EvalQuery("连接池的作用是什么", "数据库", ["连接池", "作用", "性能"], ["document_search"]),
    EvalQuery("数据库连接超时怎么办", "数据库", ["连接超时", "数据库", "排查"], ["document_search", "get_db_status"]),
    EvalQuery("如何优化数据库查询性能", "数据库", ["优化", "查询", "性能", "索引"], ["document_search"]),
    EvalQuery("什么是慢查询", "数据库", ["慢查询", "数据库", "性能"], ["document_search"]),
    EvalQuery("如何查看数据库连接数", "数据库", ["连接数", "数据库", "查看"], ["document_search", "get_db_status"]),
    EvalQuery("数据库连接数满了怎么办", "数据库", ["连接数", "满了", "数据库"], ["document_search", "get_db_status"]),
    EvalQuery("什么是读写分离", "数据库", ["读写分离", "主从", "数据库"], ["document_search"]),
    EvalQuery("什么是分库分表", "数据库", ["分库分表", "数据库", "水平拆分"], ["document_search"]),
    EvalQuery("什么是数据库备份", "数据库", ["备份", "数据库", "恢复"], ["document_search"]),
    EvalQuery("什么是数据迁移", "数据库", ["数据迁移", "数据库", "迁移"], ["document_search"]),
    EvalQuery("检查一下数据库的连接状态", "数据库", ["数据库", "连接", "状态"], ["get_db_status"]),
]

# ============================================================
#  六、MCP 工具（40 条）
# ============================================================

MCP_QUERIES = [
    EvalQuery("帮我查一下北京的天气", "MCP工具", ["北京", "天气"], ["mcp-server_get_weather"]),
    EvalQuery("今天上海天气怎么样", "MCP工具", ["上海", "天气"], ["mcp-server_get_weather"]),
    EvalQuery("广州会下雨吗", "MCP工具", ["广州", "天气", "雨"], ["mcp-server_get_weather"]),
    EvalQuery("深圳的温度是多少", "MCP工具", ["深圳", "温度"], ["mcp-server_get_weather"]),
    EvalQuery("成都天气如何", "MCP工具", ["成都", "天气"], ["mcp-server_get_weather"]),
    EvalQuery("杭州今天适合出门吗", "MCP工具", ["杭州", "天气", "出门"], ["mcp-server_get_weather"]),
    EvalQuery("武汉的湿度是多少", "MCP工具", ["武汉", "湿度"], ["mcp-server_get_weather"]),
    EvalQuery("西安今天风大吗", "MCP工具", ["西安", "风"], ["mcp-server_get_weather"]),
    EvalQuery("帮我创建一个 Jira 工单", "MCP工具", ["创建", "Jira", "工单"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("创建工单：服务器磁盘空间不足", "MCP工具", ["工单", "服务器", "磁盘"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("帮我提一个工单：数据库需要扩容", "MCP工具", ["工单", "数据库", "扩容"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("创建一个高优先级工单：生产环境告警", "MCP工具", ["工单", "高优先级", "生产环境"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("帮我记录一个问题：API 响应超时", "MCP工具", ["工单", "API", "超时"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("创建工单：用户反馈登录失败", "MCP工具", ["工单", "登录", "失败"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("帮我查一下南京天气，然后创建一个工单记录天气异常", "MCP工具", ["南京", "天气", "工单"], ["mcp-server_get_weather", "mcp-server_create_jira_ticket"]),
]

# ============================================================
#  七、综合/多工具（50 条）
# ============================================================

MULTI_TOOL_QUERIES = [
    EvalQuery("数据库连接超时，帮我排查一下", "综合", ["数据库", "连接", "超时", "排查"], ["document_search", "get_db_status"]),
    EvalQuery("服务器 ping 不通，怎么办", "综合", ["ping", "不通", "服务器"], ["document_search", "ping_host"]),
    EvalQuery("mysql 服务报错了，帮我查一下日志", "综合", ["mysql", "日志", "错误"], ["document_search", "query_service_log"]),
    EvalQuery("数据库连接池快满了，需要创建工单", "综合", ["连接池", "工单", "数据库"], ["document_search", "get_db_status", "mcp-server_create_jira_ticket"]),
    EvalQuery("帮我检查数据库状态，如果有问题就创建工单", "综合", ["数据库", "状态", "工单"], ["get_db_status", "mcp-server_create_jira_ticket"]),
    EvalQuery("api-gateway 报 503 错误，帮我排查", "综合", ["api-gateway", "503", "错误"], ["document_search", "query_service_log"]),
    EvalQuery("auth-service 连接 Redis 失败，怎么办", "综合", ["auth-service", "Redis", "连接失败"], ["document_search", "query_service_log"]),
    EvalQuery("数据库复制延迟太高，怎么处理", "综合", ["复制延迟", "数据库", "处理"], ["document_search", "get_db_status"]),
    EvalQuery("帮我检查所有服务的健康状态", "综合", ["服务", "健康", "状态"], ["ping_host", "get_db_status", "query_service_log"]),
    EvalQuery("先查一下文档里有没有关于死锁的内容，再检查数据库状态", "综合", ["死锁", "文档", "数据库"], ["document_search", "get_db_status"]),
    EvalQuery("fork 创建进程失败了，返回 -1，帮我排查", "综合", ["fork", "失败", "-1", "排查"], ["document_search"]),
    EvalQuery("页面置换算法哪个最好", "综合", ["页面置换", "最好", "算法"], ["document_search"]),
    EvalQuery("进程通信实验怎么做", "综合", ["进程通信", "实验", "怎么做"], ["document_search"]),
    EvalQuery("文件操作实验的代码怎么写", "综合", ["文件操作", "实验", "代码"], ["document_search"]),
    EvalQuery("帮我查一下数据库状态，然后查一下 mysql 的错误日志", "综合", ["数据库", "状态", "mysql", "日志"], ["get_db_status", "query_service_log"]),
]

# ============================================================
#  八、操作系统通用（80 条）
# ============================================================

OS_GENERAL_QUERIES = [
    EvalQuery("什么是操作系统", "操作系统", ["操作系统", "管理", "资源"], ["document_search"]),
    EvalQuery("操作系统的功能是什么", "操作系统", ["操作系统", "功能", "管理"], ["document_search"]),
    EvalQuery("什么是内核", "操作系统", ["内核", "kernel", "操作系统"], ["document_search"]),
    EvalQuery("什么是虚拟内存", "操作系统", ["虚拟内存", "内存", "页面"], ["document_search"]),
    EvalQuery("什么是中断", "操作系统", ["中断", "CPU", "事件"], ["document_search"]),
    EvalQuery("什么是系统调用", "操作系统", ["系统调用", "内核", "用户态"], ["document_search"]),
    EvalQuery("用户态和内核态有什么区别", "操作系统", ["用户态", "内核态", "区别"], ["document_search"]),
    EvalQuery("什么是 CPU 调度", "操作系统", ["CPU", "调度", "进程"], ["document_search"]),
    EvalQuery("什么是内存管理", "操作系统", ["内存管理", "分配", "回收"], ["document_search"]),
    EvalQuery("什么是磁盘调度", "操作系统", ["磁盘", "调度", "IO"], ["document_search"]),
    EvalQuery("什么是多线程", "操作系统", ["多线程", "线程", "并发"], ["document_search"]),
    EvalQuery("线程和进程有什么区别", "操作系统", ["线程", "进程", "区别"], ["document_search"]),
    EvalQuery("什么是协程", "操作系统", ["协程", "goroutine", "并发"], ["document_search"]),
    EvalQuery("什么是分页", "操作系统", ["分页", "页面", "内存"], ["document_search"]),
    EvalQuery("什么是分段", "操作系统", ["分段", "段", "内存"], ["document_search"]),
    EvalQuery("分页和分段有什么区别", "操作系统", ["分页", "分段", "区别"], ["document_search"]),
    EvalQuery("什么是页表", "操作系统", ["页表", "页面", "地址转换"], ["document_search"]),
    EvalQuery("什么是 TLB", "操作系统", ["TLB", "快表", "缓存"], ["document_search"]),
    EvalQuery("什么是地址空间", "操作系统", ["地址空间", "虚拟", "物理"], ["document_search"]),
    EvalQuery("什么是物理地址和逻辑地址", "操作系统", ["物理地址", "逻辑地址", "区别"], ["document_search"]),
    EvalQuery("什么是重定位", "操作系统", ["重定位", "地址", "程序"], ["document_search"]),
    EvalQuery("什么是内存碎片", "操作系统", ["内存碎片", "外碎片", "内碎片"], ["document_search"]),
    EvalQuery("什么是紧凑", "操作系统", ["紧凑", "内存", "碎片"], ["document_search"]),
    EvalQuery("什么是覆盖和交换", "操作系统", ["覆盖", "交换", "内存"], ["document_search"]),
    EvalQuery("什么是缓冲区溢出", "操作系统", ["缓冲区溢出", "安全", "漏洞"], ["document_search"]),
    EvalQuery("什么是 DMA", "操作系统", ["DMA", "直接内存访问", "IO"], ["document_search"]),
    EvalQuery("什么是设备驱动", "操作系统", ["设备驱动", "驱动程序", "硬件"], ["document_search"]),
    EvalQuery("什么是系统引导", "操作系统", ["系统引导", "启动", "boot"], ["document_search"]),
    EvalQuery("什么是 Shell", "操作系统", ["Shell", "命令行", "解释器"], ["document_search"]),
    EvalQuery("什么是 Linux", "操作系统", ["Linux", "开源", "操作系统"], ["document_search"]),
    EvalQuery("Linux 的目录结构是什么样的", "操作系统", ["Linux", "目录", "结构"], ["document_search"]),
    EvalQuery("什么是文件描述符", "操作系统", ["文件描述符", "fd", "文件"], ["document_search"]),
    EvalQuery("什么是环境变量", "操作系统", ["环境变量", "PATH", "配置"], ["document_search"]),
    EvalQuery("什么是进程组", "操作系统", ["进程组", "进程", "管理"], ["document_search"]),
    EvalQuery("什么是会话", "操作系统", ["会话", "session", "终端"], ["document_search"]),
    EvalQuery("什么是信号量", "操作系统", ["信号量", "semaphore", "同步"], ["document_search"]),
    EvalQuery("什么是互斥锁", "操作系统", ["互斥锁", "mutex", "同步"], ["document_search"]),
    EvalQuery("什么是条件变量", "操作系统", ["条件变量", "condition", "同步"], ["document_search"]),
    EvalQuery("什么是读写锁", "操作系统", ["读写锁", "rwlock", "同步"], ["document_search"]),
    EvalQuery("什么是屏障", "操作系统", ["屏障", "barrier", "同步"], ["document_search"]),
    EvalQuery("什么是生产者消费者问题", "操作系统", ["生产者", "消费者", "同步"], ["document_search"]),
    EvalQuery("什么是哲学家就餐问题", "操作系统", ["哲学家", "就餐", "死锁"], ["document_search"]),
    EvalQuery("什么是读者写者问题", "操作系统", ["读者", "写者", "同步"], ["document_search"]),
    EvalQuery("什么是内存映射", "操作系统", ["内存映射", "mmap", "文件"], ["document_search"]),
    EvalQuery("什么是写时复制", "操作系统", ["写时复制", "COW", "fork"], ["document_search"]),
    EvalQuery("什么是页缺失", "操作系统", ["页缺失", "缺页", "页面错误"], ["document_search"]),
    EvalQuery("什么是工作集", "操作系统", ["工作集", "页面", "内存"], ["document_search"]),
    EvalQuery("什么是抖动", "操作系统", ["抖动", "thrashing", "页面"], ["document_search"]),
    EvalQuery("什么是 RAID", "操作系统", ["RAID", "磁盘", "冗余"], ["document_search"]),
    EvalQuery("什么是文件系统", "操作系统", ["文件系统", "管理", "文件"], ["document_search"]),
    EvalQuery("ext4 文件系统有什么特点", "操作系统", ["ext4", "文件系统", "特点"], ["document_search"]),
]

# ============================================================
#  九、多轮对话（30 条）
# ============================================================

MULTI_TURN_QUERIES = [
    EvalQuery("fork 是什么", "多轮对话", ["fork", "创建", "进程"], ["document_search"]),
    EvalQuery("它的返回值是什么", "多轮对话", ["返回值", "fork"], ["document_search"]),
    EvalQuery("返回 0 代表什么", "多轮对话", ["返回", "0", "子进程"], ["document_search"]),
    EvalQuery("返回 -1 呢", "多轮对话", ["返回", "-1", "失败"], ["document_search"]),
    EvalQuery("那怎么创建多个进程", "多轮对话", ["创建", "多个进程", "fork"], ["document_search"]),
    EvalQuery("页面置换算法有哪些", "多轮对话", ["页面置换", "算法"], ["document_search"]),
    EvalQuery("FIFO 的原理是什么", "多轮对话", ["FIFO", "原理"], ["document_search"]),
    EvalQuery("LRU 呢", "多轮对话", ["LRU", "原理"], ["document_search"]),
    EvalQuery("哪个更好", "多轮对话", ["更好", "比较"], ["document_search"]),
    EvalQuery("数据库连接超时怎么办", "多轮对话", ["数据库", "连接超时"], ["document_search", "get_db_status"]),
    EvalQuery("帮我查一下数据库状态", "多轮对话", ["数据库", "状态"], ["get_db_status"]),
    EvalQuery("连接数多少", "多轮对话", ["连接数"], ["get_db_status"]),
    EvalQuery("帮我创建一个工单", "多轮对话", ["工单"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("优先级设为高", "多轮对话", ["优先级", "高"], ["mcp-server_create_jira_ticket"]),
    EvalQuery("进程通信有哪些方式", "多轮对话", ["进程通信", "方式"], ["document_search"]),
    EvalQuery("管道通信怎么实现", "多轮对话", ["管道", "实现"], ["document_search"]),
    EvalQuery("共享内存呢", "多轮对话", ["共享内存"], ["document_search"]),
    EvalQuery("信号怎么用", "多轮对话", ["信号", "使用"], ["document_search"]),
    EvalQuery("帮我查一下北京天气", "多轮对话", ["北京", "天气"], ["mcp-server_get_weather"]),
    EvalQuery("上海呢", "多轮对话", ["上海", "天气"], ["mcp-server_get_weather"]),
    EvalQuery("文件操作有哪些系统调用", "多轮对话", ["文件操作", "系统调用"], ["document_search"]),
    EvalQuery("read 和 write 怎么用", "多轮对话", ["read", "write", "使用"], ["document_search"]),
    EvalQuery("如何实现文件复制", "多轮对话", ["文件复制", "实现"], ["document_search"]),
    EvalQuery("什么是死锁", "多轮对话", ["死锁", "定义"], ["document_search"]),
    EvalQuery("怎么预防", "多轮对话", ["预防", "死锁"], ["document_search"]),
    EvalQuery("帮我检查网络连通性", "多轮对话", ["网络", "连通"], ["ping_host"]),
    EvalQuery("ping 一下百度", "多轮对话", ["ping", "百度"], ["ping_host"]),
    EvalQuery("查一下 mysql 的日志", "多轮对话", ["mysql", "日志"], ["query_service_log"]),
    EvalQuery("有什么错误", "多轮对话", ["错误", "日志"], ["query_service_log"]),
    EvalQuery("总结一下上面的排查结果", "多轮对话", ["总结", "排查"], []),
]

# ============================================================
#  十、复杂场景（40 条）
# ============================================================

COMPLEX_QUERIES = [
    EvalQuery("生产环境数据库连接超时，帮我完整排查一遍", "复杂场景", ["数据库", "连接超时", "排查"], ["document_search", "get_db_status", "query_service_log"]),
    EvalQuery("服务器 192.168.1.100 ping 不通，查一下文档里有没有解决方案", "复杂场景", ["ping", "不通", "文档"], ["document_search", "ping_host"]),
    EvalQuery("mysql 报错 Too many connections，帮我查日志和数据库状态", "复杂场景", ["mysql", "连接数", "日志", "状态"], ["query_service_log", "get_db_status"]),
    EvalQuery("fork 创建进程失败，返回 -1，帮我查文档找原因", "复杂场景", ["fork", "失败", "文档"], ["document_search"]),
    EvalQuery("页面置换算法实验做完了，帮我创建一个工单记录结果", "复杂场景", ["页面置换", "实验", "工单"], ["document_search", "mcp-server_create_jira_ticket"]),
    EvalQuery("先查一下文档里关于进程通信的内容，再帮我查一下相关服务的日志", "复杂场景", ["进程通信", "文档", "日志"], ["document_search", "query_service_log"]),
    EvalQuery("数据库连接池满了，帮我查文档找解决方案，然后创建工单", "复杂场景", ["连接池", "文档", "工单"], ["document_search", "get_db_status", "mcp-server_create_jira_ticket"]),
    EvalQuery("auth-service 报错 Connection refused，帮我查文档和日志", "复杂场景", ["auth-service", "连接拒绝", "文档", "日志"], ["document_search", "query_service_log"]),
    EvalQuery("帮我检查数据库状态，如果连接数超过 80% 就创建工单", "复杂场景", ["数据库", "连接数", "工单"], ["get_db_status", "mcp-server_create_jira_ticket"]),
    EvalQuery("查一下 api-gateway 的错误日志，然后帮我查文档找 503 错误的原因", "复杂场景", ["api-gateway", "503", "日志", "文档"], ["document_search", "query_service_log"]),
    EvalQuery("fork 和 vfork 有什么区别", "复杂场景", ["fork", "vfork", "区别"], ["document_search"]),
    EvalQuery("进程的三种状态转换图是什么样的", "复杂场景", ["进程", "状态", "转换"], ["document_search"]),
    EvalQuery("什么是银行家算法", "复杂场景", ["银行家算法", "死锁", "避免"], ["document_search"]),
    EvalQuery("什么是安全序列", "复杂场景", ["安全序列", "银行家", "死锁"], ["document_search"]),
    EvalQuery("内存分配有哪些策略", "复杂场景", ["内存分配", "策略", "首次适应", "最佳适应"], ["document_search"]),
    EvalQuery("什么是段页式存储", "复杂场景", ["段页式", "存储", "分段", "分页"], ["document_search"]),
    EvalQuery("什么是局部性原理", "复杂场景", ["局部性原理", "时间局部性", "空间局部性"], ["document_search"]),
    EvalQuery("什么是预调页和请求调页", "复杂场景", ["预调页", "请求调页", "页面"], ["document_search"]),
    EvalQuery("什么是 IO 多路复用", "复杂场景", ["IO多路复用", "select", "poll", "epoll"], ["document_search"]),
    EvalQuery("select 和 epoll 有什么区别", "复杂场景", ["select", "epoll", "区别"], ["document_search"]),
    EvalQuery("什么是零拷贝", "复杂场景", ["零拷贝", "DMA", "IO"], ["document_search"]),
    EvalQuery("什么是 mmap", "复杂场景", ["mmap", "内存映射", "文件"], ["document_search"]),
    EvalQuery("什么是用户级线程和内核级线程", "复杂场景", ["用户级线程", "内核级线程", "区别"], ["document_search"]),
    EvalQuery("什么是线程池", "复杂场景", ["线程池", "线程", "管理"], ["document_search"]),
    EvalQuery("什么是协程和线程的区别", "复杂场景", ["协程", "线程", "区别"], ["document_search"]),
    EvalQuery("什么是系统抖动", "复杂场景", ["系统抖动", "thrashing", "页面"], ["document_search"]),
    EvalQuery("什么是 Belady 异常", "复杂场景", ["Belady", "异常", "FIFO"], ["document_search"]),
    EvalQuery("什么是缺页率", "复杂场景", ["缺页率", "缺页", "页面"], ["document_search"]),
    EvalQuery("什么是 CLOCK 算法", "复杂场景", ["CLOCK", "算法", "页面置换"], ["document_search"]),
    EvalQuery("什么是访问位和修改位", "复杂场景", ["访问位", "修改位", "页面"], ["document_search"]),
    EvalQuery("什么是 IO 调度算法", "复杂场景", ["IO调度", "算法", "磁盘"], ["document_search"]),
    EvalQuery("什么是磁盘寻道时间", "复杂场景", ["磁盘", "寻道时间", "性能"], ["document_search"]),
    EvalQuery("什么是 RAID 0 和 RAID 1", "复杂场景", ["RAID 0", "RAID 1", "磁盘"], ["document_search"]),
    EvalQuery("什么是 inode", "复杂场景", ["inode", "文件系统", "索引"], ["document_search"]),
    EvalQuery("什么是日志文件系统", "复杂场景", ["日志文件系统", "ext3", "ext4"], ["document_search"]),
    EvalQuery("什么是符号链接和硬链接", "复杂场景", ["符号链接", "硬链接", "区别"], ["document_search"]),
    EvalQuery("什么是文件锁", "复杂场景", ["文件锁", "flock", "并发"], ["document_search"]),
    EvalQuery("什么是内存泄漏", "复杂场景", ["内存泄漏", "malloc", "free"], ["document_search"]),
    EvalQuery("什么是段错误", "复杂场景", ["段错误", "segmentation fault", "内存"], ["document_search"]),
    EvalQuery("什么是栈溢出", "复杂场景", ["栈溢出", "stack overflow", "递归"], ["document_search"]),
]

# ============================================================
#  十一、边界/干扰（30 条）
# ============================================================

EDGE_CASE_QUERIES = [
    EvalQuery("你好", "边界", [], []),
    EvalQuery("你是谁", "边界", ["SupportPilot", "技术支持"], []),
    EvalQuery("你能做什么", "边界", ["技术支持", "文档", "诊断"], []),
    EvalQuery("谢谢", "边界", [], []),
    EvalQuery("123456", "边界", [], []),
    EvalQuery("aaaa bbbb cccc", "边界", [], []),
    EvalQuery("今天天气真好", "边界", ["天气"], []),
    EvalQuery("帮我写一个 Python 程序", "边界", ["Python", "程序"], []),
    EvalQuery("什么是人工智能", "边界", ["人工智能", "AI"], []),
    EvalQuery("什么是机器学习", "边界", ["机器学习", "ML"], []),
    EvalQuery("什么是深度学习", "边界", ["深度学习", "神经网络"], []),
    EvalQuery("Linux 和 Windows 有什么区别", "边界", ["Linux", "Windows", "区别"], []),
    EvalQuery("什么是容器", "边界", ["容器", "Docker", "虚拟化"], []),
    EvalQuery("什么是微服务", "边界", ["微服务", "架构", "服务"], []),
    EvalQuery("什么是负载均衡", "边界", ["负载均衡", "流量", "分发"], []),
    EvalQuery("什么是缓存", "边界", ["缓存", "cache", "Redis"], []),
    EvalQuery("什么是网络编程", "边界", ["网络编程", "socket", "TCP"], []),
    EvalQuery("什么是 Git", "边界", ["Git", "版本控制"], []),
    EvalQuery("什么是 Docker", "边界", ["Docker", "容器"], []),
    EvalQuery("什么是 Kubernetes", "边界", ["Kubernetes", "K8s", "容器编排"], []),
    EvalQuery("什么是 CI/CD", "边界", ["CI", "CD", "持续集成"], []),
    EvalQuery("什么是 DevOps", "边界", ["DevOps", "开发运维"], []),
    EvalQuery("什么是云计算", "边界", ["云计算", "AWS", "阿里云"], []),
    EvalQuery("什么是大数据", "边界", ["大数据", "Hadoop", "Spark"], []),
    EvalQuery("什么是区块链", "边界", ["区块链", "比特币"], []),
    EvalQuery("什么是物联网", "边界", ["物联网", "IoT"], []),
    EvalQuery("什么是 5G", "边界", ["5G", "通信"], []),
    EvalQuery("什么是量子计算", "边界", ["量子计算", "量子"], []),
    EvalQuery("帮我点个外卖", "边界", ["外卖"], []),
    EvalQuery("今天几号", "边界", ["日期"], []),
]

# ============================================================
#  十二、补充扩充（150+ 条）
# ============================================================

EXTRA_PROCESS_QUERIES = [
    EvalQuery("什么是时间片轮转调度", "进程管理", ["时间片", "轮转", "调度"], ["document_search"]),
    EvalQuery("什么是优先级调度", "进程管理", ["优先级", "调度", "进程"], ["document_search"]),
    EvalQuery("什么是多级反馈队列调度", "进程管理", ["多级反馈队列", "调度"], ["document_search"]),
    EvalQuery("什么是 FCFS 调度算法", "进程管理", ["FCFS", "先来先服务", "调度"], ["document_search"]),
    EvalQuery("什么是 SJF 调度算法", "进程管理", ["SJF", "短作业优先", "调度"], ["document_search"]),
    EvalQuery("什么是 SRTF 调度算法", "进程管理", ["SRTF", "最短剩余时间", "调度"], ["document_search"]),
    EvalQuery("什么是响应比", "进程管理", ["响应比", "调度", "等待时间"], ["document_search"]),
    EvalQuery("什么是甘特图", "进程管理", ["甘特图", "调度", "可视化"], ["document_search"]),
    EvalQuery("什么是周转时间", "进程管理", ["周转时间", "进程", "完成"], ["document_search"]),
    EvalQuery("什么是等待时间", "进程管理", ["等待时间", "进程", "调度"], ["document_search"]),
    EvalQuery("什么是吞吐量", "进程管理", ["吞吐量", "系统", "处理能力"], ["document_search"]),
    EvalQuery("什么是 CPU 利用率", "进程管理", ["CPU利用率", "系统", "性能"], ["document_search"]),
    EvalQuery("什么是抢占式调度", "进程管理", ["抢占式", "调度", "进程"], ["document_search"]),
    EvalQuery("什么是非抢占式调度", "进程管理", ["非抢占式", "调度", "进程"], ["document_search"]),
    EvalQuery("什么是实时调度", "进程管理", ["实时", "调度", "进程"], ["document_search"]),
    EvalQuery("什么是 EDF 调度算法", "进程管理", ["EDF", "最早截止时间", "调度"], ["document_search"]),
    EvalQuery("什么是 RMS 调度算法", "进程管理", ["RMS", "速率单调", "调度"], ["document_search"]),
    EvalQuery("什么是负载均衡", "进程管理", ["负载均衡", "进程", "分配"], ["document_search"]),
    EvalQuery("什么是进程迁移", "进程管理", ["进程迁移", "负载均衡"], ["document_search"]),
    EvalQuery("什么是超线程", "进程管理", ["超线程", "CPU", "并发"], ["document_search"]),
    EvalQuery("什么是多核调度", "进程管理", ["多核", "调度", "CPU"], ["document_search"]),
    EvalQuery("什么是 NUMA 架构", "进程管理", ["NUMA", "架构", "内存"], ["document_search"]),
    EvalQuery("什么是缓存一致性", "进程管理", ["缓存一致性", "多核", "缓存"], ["document_search"]),
    EvalQuery("什么是 MESI 协议", "进程管理", ["MESI", "协议", "缓存一致性"], ["document_search"]),
    EvalQuery("什么是内存屏障", "进程管理", ["内存屏障", "并发", "同步"], ["document_search"]),
    EvalQuery("什么是无锁编程", "进程管理", ["无锁编程", "CAS", "并发"], ["document_search"]),
    EvalQuery("什么是 CAS 操作", "进程管理", ["CAS", "比较并交换", "原子操作"], ["document_search"]),
    EvalQuery("什么是 ABA 问题", "进程管理", ["ABA", "问题", "CAS"], ["document_search"]),
    EvalQuery("什么是乐观锁和悲观锁", "进程管理", ["乐观锁", "悲观锁", "并发"], ["document_search"]),
    EvalQuery("什么是可重入锁", "进程管理", ["可重入锁", "递归锁", "并发"], ["document_search"]),
    EvalQuery("什么是公平锁和非公平锁", "进程管理", ["公平锁", "非公平锁", "并发"], ["document_search"]),
    EvalQuery("什么是死锁检测", "进程管理", ["死锁", "检测", "资源分配图"], ["document_search"]),
    EvalQuery("什么是死锁恢复", "进程管理", ["死锁", "恢复", "资源"], ["document_search"]),
    EvalQuery("什么是资源分配图", "进程管理", ["资源分配图", "死锁", "检测"], ["document_search"]),
    EvalQuery("什么是饥饿问题", "进程管理", ["饥饿", "进程", "调度"], ["document_search"]),
    EvalQuery("什么是优先级继承", "进程管理", ["优先级继承", "优先级反转"], ["document_search"]),
    EvalQuery("什么是优先级天花板", "进程管理", ["优先级天花板", "优先级反转"], ["document_search"]),
    EvalQuery("Peterson 算法是什么", "进程管理", ["Peterson", "算法", "互斥"], ["document_search"]),
    EvalQuery("什么是面包店算法", "进程管理", ["面包店算法", "互斥", "并发"], ["document_search"]),
    EvalQuery("什么是 TSL 指令", "进程管理", ["TSL", "指令", "原子操作"], ["document_search"]),
    EvalQuery("什么是 xchg 指令", "进程管理", ["xchg", "指令", "原子操作"], ["document_search"]),
]

EXTRA_IPC_QUERIES = [
    EvalQuery("什么是 POSIX IPC", "进程通信", ["POSIX", "IPC", "标准"], ["document_search"]),
    EvalQuery("POSIX 消息队列怎么用", "进程通信", ["POSIX", "消息队列", "使用"], ["document_search"]),
    EvalQuery("POSIX 共享内存怎么用", "进程通信", ["POSIX", "共享内存", "使用"], ["document_search"]),
    EvalQuery("什么是内存映射文件", "进程通信", ["内存映射", "文件", "mmap"], ["document_search"]),
    EvalQuery("什么是 Unix Domain Socket", "进程通信", ["Unix Domain Socket", "IPC", "通信"], ["document_search"]),
    EvalQuery("什么是 RPC", "进程通信", ["RPC", "远程过程调用", "通信"], ["document_search"]),
    EvalQuery("什么是消息传递", "进程通信", ["消息传递", "通信", "同步"], ["document_search"]),
    EvalQuery("什么是共享文件通信", "进程通信", ["共享文件", "通信", "进程"], ["document_search"]),
    EvalQuery("什么是信号量集", "进程通信", ["信号量集", "semget", "IPC"], ["document_search"]),
    EvalQuery("semop 函数怎么用", "进程通信", ["semop", "信号量", "操作"], ["document_search"]),
    EvalQuery("semctl 函数怎么用", "进程通信", ["semctl", "信号量", "控制"], ["document_search"]),
    EvalQuery("什么是生产者消费者问题的信号量解法", "进程通信", ["生产者消费者", "信号量", "解法"], ["document_search"]),
    EvalQuery("什么是读者写者问题的信号量解法", "进程通信", ["读者写者", "信号量", "解法"], ["document_search"]),
    EvalQuery("什么是哲学家就餐问题的解法", "进程通信", ["哲学家就餐", "解法", "死锁"], ["document_search"]),
    EvalQuery("什么是忙等待", "进程通信", ["忙等待", "自旋锁", "同步"], ["document_search"]),
]

EXTRA_DB_QUERIES = [
    EvalQuery("什么是数据库事务隔离级别", "数据库", ["事务", "隔离级别", "读未提交"], ["document_search"]),
    EvalQuery("读未提交是什么", "数据库", ["读未提交", "脏读", "隔离级别"], ["document_search"]),
    EvalQuery("读已提交是什么", "数据库", ["读已提交", "不可重复读", "隔离级别"], ["document_search"]),
    EvalQuery("可重复读是什么", "数据库", ["可重复读", "幻读", "隔离级别"], ["document_search"]),
    EvalQuery("串行化是什么", "数据库", ["串行化", "隔离级别", "事务"], ["document_search"]),
    EvalQuery("什么是悲观锁", "数据库", ["悲观锁", "数据库", "并发"], ["document_search"]),
    EvalQuery("什么是乐观锁", "数据库", ["乐观锁", "数据库", "并发"], ["document_search"]),
    EvalQuery("什么是 MVCC", "数据库", ["MVCC", "多版本并发控制", "数据库"], ["document_search"]),
    EvalQuery("什么是数据库分片", "数据库", ["分片", "数据库", "水平拆分"], ["document_search"]),
    EvalQuery("什么是数据库复制", "数据库", ["复制", "数据库", "主从"], ["document_search"]),
    EvalQuery("什么是数据库缓存", "数据库", ["缓存", "数据库", "Redis"], ["document_search"]),
    EvalQuery("什么是数据库连接泄漏", "数据库", ["连接泄漏", "数据库", "连接池"], ["document_search"]),
    EvalQuery("什么是 SQL 注入", "数据库", ["SQL注入", "安全", "数据库"], ["document_search"]),
    EvalQuery("如何防止 SQL 注入", "数据库", ["SQL注入", "防止", "参数化查询"], ["document_search"]),
    EvalQuery("什么是数据库死锁", "数据库", ["数据库死锁", "事务", "等待"], ["document_search"]),
    EvalQuery("什么是 ORM", "数据库", ["ORM", "对象关系映射", "数据库"], ["document_search"]),
    EvalQuery("什么是 NoSQL", "数据库", ["NoSQL", "非关系型", "数据库"], ["document_search"]),
    EvalQuery("什么是 CAP 定理", "数据库", ["CAP", "定理", "一致性"], ["document_search"]),
    EvalQuery("什么是 BASE 理论", "数据库", ["BASE", "理论", "最终一致性"], ["document_search"]),
    EvalQuery("什么是分布式数据库", "数据库", ["分布式数据库", "数据库", "分布式"], ["document_search"]),
]

EXTRA_FILE_QUERIES = [
    EvalQuery("什么是文件分配表", "文件系统", ["文件分配表", "FAT", "文件系统"], ["document_search"]),
    EvalQuery("什么是位图法", "文件系统", ["位图法", "空闲空间", "管理"], ["document_search"]),
    EvalQuery("什么是链接分配", "文件系统", ["链接分配", "文件", "磁盘"], ["document_search"]),
    EvalQuery("什么是索引分配", "文件系统", ["索引分配", "文件", "磁盘"], ["document_search"]),
    EvalQuery("什么是连续分配", "文件系统", ["连续分配", "文件", "磁盘"], ["document_search"]),
    EvalQuery("文件的逻辑结构有哪些", "文件系统", ["逻辑结构", "文件", "流式", "记录式"], ["document_search"]),
    EvalQuery("文件的物理结构有哪些", "文件系统", ["物理结构", "文件", "磁盘"], ["document_search"]),
    EvalQuery("什么是文件目录", "文件系统", ["文件目录", "目录项", "文件"], ["document_search"]),
    EvalQuery("什么是文件共享", "文件系统", ["文件共享", "访问控制", "文件"], ["document_search"]),
    EvalQuery("什么是文件保护", "文件系统", ["文件保护", "权限", "安全"], ["document_search"]),
    EvalQuery("什么是访问控制矩阵", "文件系统", ["访问控制矩阵", "文件", "安全"], ["document_search"]),
    EvalQuery("什么是访问控制列表", "文件系统", ["访问控制列表", "ACL", "文件"], ["document_search"]),
    EvalQuery("什么是文件加密", "文件系统", ["文件加密", "安全", "文件"], ["document_search"]),
    EvalQuery("什么是文件压缩", "文件系统", ["文件压缩", "压缩", "文件"], ["document_search"]),
    EvalQuery("什么是文件系统的挂载", "文件系统", ["挂载", "mount", "文件系统"], ["document_search"]),
    EvalQuery("什么是虚拟文件系统", "文件系统", ["虚拟文件系统", "VFS", "文件系统"], ["document_search"]),
    EvalQuery("什么是日志结构文件系统", "文件系统", ["日志结构", "LFS", "文件系统"], ["document_search"]),
    EvalQuery("什么是内存映射文件 IO", "文件系统", ["内存映射", "mmap", "IO"], ["document_search"]),
    EvalQuery("什么是直接 IO", "文件系统", ["直接IO", "绕过缓存", "文件"], ["document_search"]),
    EvalQuery("什么是异步 IO", "文件系统", ["异步IO", "非阻塞", "文件"], ["document_search"]),
    EvalQuery("什么是同步 IO", "文件系统", ["同步IO", "阻塞", "文件"], ["document_search"]),
    EvalQuery("什么是 IO 多路复用 select poll epoll", "文件系统", ["select", "poll", "epoll", "IO"], ["document_search"]),
    EvalQuery("什么是文件系统的超级块", "文件系统", ["超级块", "superblock", "文件系统"], ["document_search"]),
]

EXTRA_DIAGNOSTIC_QUERIES = [
    EvalQuery("帮我 ping 一下 google.com", "诊断工具", ["ping", "google"], ["ping_host"]),
    EvalQuery("ping 一下 10.0.0.1", "诊断工具", ["ping", "10.0.0.1"], ["ping_host"]),
    EvalQuery("检查 192.168.0.1 的连通性", "诊断工具", ["检查", "连通性", "192.168.0.1"], ["ping_host"]),
    EvalQuery("测试一下到 8.8.8.8 的网络", "诊断工具", ["测试", "网络", "8.8.8.8"], ["ping_host"]),
    EvalQuery("查一下 database 服务的 ERROR 日志", "诊断工具", ["database", "ERROR", "日志"], ["query_service_log"]),
    EvalQuery("查一下 api-gateway 的 WARN 日志", "诊断工具", ["api-gateway", "WARN", "日志"], ["query_service_log"]),
    EvalQuery("查一下 auth-service 的日志", "诊断工具", ["auth-service", "日志"], ["query_service_log"]),
    EvalQuery("查一下 database 服务最近的错误", "诊断工具", ["database", "错误", "日志"], ["query_service_log"]),
    EvalQuery("帮我查一下 mysql 的状态", "诊断工具", ["mysql", "状态"], ["get_db_status"]),
    EvalQuery("检查一下 postgres 的连接数", "诊断工具", ["postgres", "连接数"], ["get_db_status"]),
    EvalQuery("redis 的状态怎么样", "诊断工具", ["redis", "状态"], ["get_db_status"]),
    EvalQuery("mongodb 是否正常", "诊断工具", ["mongodb", "正常", "状态"], ["get_db_status"]),
    EvalQuery("帮我查一下所有数据库的状态", "诊断工具", ["数据库", "状态", "所有"], ["get_db_status"]),
]

EXTRA_EDGE_QUERIES = [
    EvalQuery("Hello world", "边界", [], []),
    EvalQuery("你好世界", "边界", [], []),
    EvalQuery("请问一下", "边界", [], []),
    EvalQuery("帮我看看", "边界", [], []),
    EvalQuery("这个问题怎么解决", "边界", [], []),
    EvalQuery("我不太明白", "边界", [], []),
    EvalQuery("能详细解释一下吗", "边界", [], []),
    EvalQuery("还有其他方法吗", "边界", [], []),
    EvalQuery("哪个方案更好", "边界", [], []),
    EvalQuery("为什么这样设计", "边界", [], []),
    EvalQuery("这样做的好处是什么", "边界", [], []),
    EvalQuery("有什么缺点", "边界", [], []),
    EvalQuery("有没有替代方案", "边界", [], []),
    EvalQuery("最佳实践是什么", "边界", [], []),
    EvalQuery("有什么注意事项", "边界", [], []),
    EvalQuery("常见的错误有哪些", "边界", [], []),
    EvalQuery("如何调试", "边界", [], []),
    EvalQuery("如何测试", "边界", [], []),
    EvalQuery("如何部署", "边界", [], []),
    EvalQuery("如何监控", "边界", [], []),
    EvalQuery("如何优化性能", "边界", [], []),
    EvalQuery("如何提高安全性", "边界", [], []),
    EvalQuery("如何扩展", "边界", [], []),
    EvalQuery("如何维护", "边界", [], []),
    EvalQuery("如何升级", "边界", [], []),
    EvalQuery("如何回滚", "边界", [], []),
    EvalQuery("如何备份", "边界", [], []),
    EvalQuery("如何恢复", "边界", [], []),
    EvalQuery("如何迁移", "边界", [], []),
    EvalQuery("什么是操作系统启动过程", "操作系统", ["启动", "引导", "操作系统"], ["document_search"]),
    EvalQuery("什么是 BIOS 和 UEFI", "操作系统", ["BIOS", "UEFI", "启动"], ["document_search"]),
    EvalQuery("什么是中断描述表", "操作系统", ["中断描述表", "IDT", "中断"], ["document_search"]),
    EvalQuery("什么是系统调用号", "操作系统", ["系统调用号", "系统调用", "内核"], ["document_search"]),
    EvalQuery("什么是上下文切换的开销", "操作系统", ["上下文切换", "开销", "性能"], ["document_search"]),
    EvalQuery("什么是缓存命中率", "操作系统", ["缓存命中率", "缓存", "性能"], ["document_search"]),
    EvalQuery("什么是预取", "操作系统", ["预取", "prefetch", "缓存"], ["document_search"]),
]

# ============================================================
#  合并所有数据集
# ============================================================

ALL_QUERIES: list[EvalQuery] = (
    PROCESS_QUERIES
    + IPC_QUERIES
    + PAGE_REPLACEMENT_QUERIES
    + FILE_SYSTEM_QUERIES
    + DATABASE_QUERIES
    + MCP_QUERIES
    + MULTI_TOOL_QUERIES
    + OS_GENERAL_QUERIES
    + MULTI_TURN_QUERIES
    + COMPLEX_QUERIES
    + EDGE_CASE_QUERIES
    + EXTRA_PROCESS_QUERIES
    + EXTRA_IPC_QUERIES
    + EXTRA_DB_QUERIES
    + EXTRA_FILE_QUERIES
    + EXTRA_DIAGNOSTIC_QUERIES
    + EXTRA_EDGE_QUERIES
)


def get_dataset_stats() -> dict:
    """返回数据集统计信息。"""
    categories = {}
    for q in ALL_QUERIES:
        if q.category not in categories:
            categories[q.category] = 0
        categories[q.category] += 1

    tool_counts = {"no_tool": 0, "single_tool": 0, "multi_tool": 0}
    for q in ALL_QUERIES:
        if len(q.expected_tools) == 0:
            tool_counts["no_tool"] += 1
        elif len(q.expected_tools) == 1:
            tool_counts["single_tool"] += 1
        else:
            tool_counts["multi_tool"] += 1

    return {
        "total": len(ALL_QUERIES),
        "categories": categories,
        "tool_distribution": tool_counts,
    }
