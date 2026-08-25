import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        # 排除虚拟环境与数据目录，避免 pip 装包/数据写入触发无效重载
        reload_excludes=[".venv", "data", "__pycache__", "*.pyc"],
    )
