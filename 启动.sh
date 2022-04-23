#!/bin/sh

TMUX_SESSION_NAME=sese_engine

if ! command -v tmux &> /dev/null
then
    	echo "找不到 tmux 啦，我们用丑一点的界面吧！"
    	python 人服务器.py &
	python 上网.py &
	python 回.py &
	while true; do python 收获服务器.py; done
    	exit
fi

echo "找到了 tmux，可以把屏幕分成四块！"

tmux new -t $TMUX_SESSION_NAME -d
tmux split-window -t $TMUX_SESSION_NAME -h
tmux split-window -t $TMUX_SESSION_NAME -v 
tmux select-pane -t $TMUX_SESSION_NAME -L 
tmux split-window -t $TMUX_SESSION_NAME -v
tmux select-pane -U -t $TMUX_SESSION_NAME
tmux send-keys -t $TMUX_SESSION_NAME.0 "python 人服务器.py" Enter
tmux send-keys -t $TMUX_SESSION_NAME.1 "python 上网.py" Enter
tmux send-keys -t $TMUX_SESSION_NAME.2 "python 回.py" Enter
tmux send-keys -t $TMUX_SESSION_NAME.3 "while true; do python 收获服务器.py; done" Enter
tmux attach -t $TMUX_SESSION_NAME
