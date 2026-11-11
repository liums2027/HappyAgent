## 2026年10月30日22:53:37
搭建agent的第一个阶段，打底；
发现的问题：
1、不知道怎么注册方法。
2、不知道方法应该在什么阶段注册进去？我一般是在实例化agent后再注册，这样是对的吗？
3、怎样是标准的方法注入的实现？
4、这个memory应该怎么设计才对？

## 2026年11月11日22:44:26
在tool的read_file中添加了对linux中link的过滤。
现在list_file的结果中不会出现link类型的内容了。
实验方式：
1、创建link
New-Item -ItemType SymbolicLink -Path "G:\AIWorkSpace\HappyCoding\test_link\external_link_2.txt" -Target "G:\outside\secret.txt"
New-Item -ItemType SymbolicLink -Path "G:\AIWorkSpace\HappyCoding\test_link\external_link_3.txt" -Target "G:\outside"
这两个一个是文件，一个是目录
然后执行list_files("G:\\AIWorkSpace\\HappyCoding")
发现打印的内容中不会出现link相关的文件