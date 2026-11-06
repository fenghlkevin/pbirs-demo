& 'C:\ProgramData\P4DemoApp\runtime\python.exe' -c "import socket; s=socket.socket(); print('default send buffer',s.getsockopt(socket.SOL_SOCKET,socket.SO_SNDBUF)); print('default receive buffer',s.getsockopt(socket.SOL_SOCKET,socket.SO_RCVBUF))"
Get-NetTCPSetting -SettingName Internet | Select-Object AutoTuningLevelLocal,CongestionProvider,InitialCongestionWindowMss
