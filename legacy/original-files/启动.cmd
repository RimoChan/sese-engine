::set http_proxy=127.0.0.1:3128
::set https_proxy=127.0.0.1:20171
start "收获服务器" cmd /c "for /l %%a in (0,0,1) do python 收获服务器.py"
start "人服务器" cmd /c "python 人服务器.py & pause"
start "上网" cmd /c "for /l %%a in (0,0,1) do python 上网.py"
start "回" cmd /c "python 回.py & pause"