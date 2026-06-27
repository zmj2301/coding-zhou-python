import logging

# 配置日志：同时输出到控制台和文件，指定格式和级别
logging.basicConfig(
    level=logging.DEBUG,  # 全局最低日志级别（低于此的不输出）
    format="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",  # 时间格式
    handlers=[
        logging.StreamHandler(),  # 输出到控制台
        logging.FileHandler("app.log", encoding="utf-8")  # 输出到文件（utf-8避免中文乱码）
    ]
)

# 使用
logging.debug("用户登录：username=test")
logging.info("数据同步完成：共100条")
logging.warning("磁盘空间不足：剩余5GB")
logging.error("接口调用失败：status_code=500")
logging.critical("服务停止：内存溢出")