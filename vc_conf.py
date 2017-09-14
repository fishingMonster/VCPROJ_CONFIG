#coding=utf-8
import os
import uuid
import xml.dom.minidom as Dom
import codecs
import tkinter
import tkinter.messagebox
from tkinter.filedialog import *
import shutil
#全局路径
tkRoot = tkinter.Tk()

# 通过绝对路径计算dst相对于src的路径
def relate_path(dst_abs_path, src_abs_path):
    list_dst=dst_abs_path.split('/')
    list_src= src_abs_path.split('/')
    for i in range(0, min(len(list_dst),len(list_src))):
        if list_dst[i]!=list_src[i]:
            break
    path_relate = '..\\'*(len(list_src)-i)
    for item in list_dst[i:]:
        path_relate += item
        path_relate += '\\'
    return path_relate

# 通过src绝对路径和dst相对路径求出dst绝对路径
def abs_path(dst_related_path, src_abs_path):
    list_dst=dst_related_path.split('\\')
    list_src= src_abs_path.split('/')

    upfolder_num=0
    for i in range(0, len(list_dst)):
        if list_dst[i]==u'..':
            upfolder_num+=1
    dst_abs_path=''
    for str in list_src[0:-upfolder_num]:
        dst_abs_path+=str
        dst_abs_path+='/'
    for str in list_dst[upfolder_num:]:
        dst_abs_path+=str
        dst_abs_path+='/'
    return dst_abs_path

#备份文件
def file_backup(file_path):
    file_info=os.path.splitext(file_path)
    shutil.copyfile(file_path,file_info[0]+u'_backup'+file_info[1])

# 创建单层文件夹节点
def ut_xml_folder_gen(this_node, abs_path, relate_path, dom):
    item_list=os.listdir(abs_path)
    for item in item_list:
        sub_abs_path= abs_path + item
        sub_relate_path = relate_path + item
        this_child_nodes = this_node.childNodes
        sub_node = this_node
        if os.path.isfile(sub_abs_path):
            if os.path.splitext(sub_abs_path)[1] in ['.c','.h','.cpp','.hpp','.cm']:
                for sub_node in this_child_nodes:
                    if sub_node.nodeName=='File' and sub_node.getAttribute('RelativePath')==sub_relate_path:
                        break
                if sub_node.nodeName=='File'and sub_node.getAttribute('RelativePath') == sub_relate_path:
                    continue
                sub_node=dom.createElement('File')
                sub_node.setAttribute('RelativePath', sub_relate_path)
                this_node.appendChild(sub_node)
        else:
            for sub_node in this_child_nodes:
                if sub_node.nodeName == 'Filter' and sub_node.getAttribute('Name') == item:
                    break
            if sub_node.nodeName != 'Filter' or sub_node.getAttribute('Name') != item:
                sub_node=dom.createElement('Filter')
                sub_node.setAttribute('Name', item)
                this_node.appendChild(sub_node)
            sub_abs_path+='/'
            sub_relate_path+='\\'
            ut_xml_folder_gen(sub_node,sub_abs_path,sub_relate_path,dom)

# 修改xml文件完成路径生成
def ut_xml_init(xml_file_path,code_folder_path,filter_uuid):
    if filter_uuid == '':
        tkinter.messagebox.showinfo(title='注意',message='请输入正确的VC筛选器唯一标识符')
        return
    if xml_file_path == '':
        tkinter.messagebox.showinfo(title='注意',message='请选择正确的VC配置文件')
        return
    if code_folder_path == '':
        tkinter.messagebox.showinfo(title='注意',message='请选择正确的代码目录')
        return
    init_relate_path=relate_path(code_folder_path,os.path.split(xml_file_path)[0])
    #更改编码格式-utf-8
    file_backup(xml_file_path)
    xml_file=open(xml_file_path,'r')
    text = xml_file.read()
    text = text.replace(u'encoding="gb2312"', u'encoding="utf-8"')
    dom = Dom.parseString(text.encode('utf-8'))

    finish_flag=0
    for code_node in dom.getElementsByTagName('Filter'):
        if code_node.hasAttribute('UniqueIdentifier') and code_node.getAttribute('UniqueIdentifier')==filter_uuid:
            ut_xml_folder_gen(code_node, code_folder_path + '/', init_relate_path, dom)
            finish_flag=1
            break
    #存储
    xml_file=open(xml_file_path,'w')
    dom.writexml(xml_file, indent='\t', newl='\n',encoding='utf-8')

    #更改编码格式-gb2312
    xml_file=open(xml_file_path,'r')
    text = xml_file.read()
    text = text.replace(u'encoding="utf-8"', u'encoding="gb2312"')
    xml_file = open(xml_file_path, 'w')
    xml_file.write(text)
    xml_file.close()
    if finish_flag == 0:
        tkinter.messagebox.showinfo(title='注意', message='没有找到UUID对应筛选器')
    else:
        tkinter.messagebox.showinfo(title='注意', message='导入成功')
        ut_xml_add_include(xml_file_path)
        ut_xml_uuid(xml_file_path)


#刷新文件&添加引用
def ut_xml_add_include(xml_file_path):
    if xml_file_path == '':
        tkinter.messagebox.showinfo(title='注意',message='请选择正确的VC配置文件')
        return
    # 更改编码格式-utf-8
    file_backup(xml_file_path)
    xml_file = open(xml_file_path, 'r')
    text = xml_file.read()
    text = text.replace(u'encoding="gb2312"', u'encoding="utf-8"')
    dom = Dom.parseString(text.encode('utf-8'))
    #记录所有include地址
    all_include_path=''
    all_include_path_list=[]
    for h_node in dom.getElementsByTagName('File'):
        h_file=h_node.getAttribute('RelativePath')
        h_path=os.path.split(h_file)[0]
        h_file_name=os.path.split(h_file)[1]
        if not os.path.isfile(abs_path(h_path,os.path.split(xml_file_path)[0])+h_file_name):
            h_node.parentNode.removeChild(h_node)
            continue
        if os.path.splitext(h_file)[1] in ['.h','.hpp'] and h_path not in all_include_path_list:
            all_include_path_list+=h_path
            all_include_path+=h_path
            all_include_path+=';'
    #找到include节点
    conf_nodes = dom.getElementsByTagName('Configuration')
    for conf_node in conf_nodes:
        for tool_node in conf_node.childNodes:
            if tool_node.nodeName == 'Tool' and tool_node.getAttribute('Name')=='VCCLCompilerTool':
                tool_node.setAttribute('AdditionalIncludeDirectories',all_include_path)

    #存储
    xml_file=open(xml_file_path,'w')
    dom.writexml(xml_file, indent='\t', newl='\n',encoding='utf-8')

    #更改编码格式-gb2312
    xml_file=open(xml_file_path,'r')
    text = xml_file.read()
    text = text.replace(u'encoding="utf-8"', u'encoding="gb2312"')
    xml_file = open(xml_file_path, 'w')
    xml_file.write(text)
    xml_file.close()
    tkinter.messagebox.showinfo(title='注意', message='刷新文件&修复引用成功')

#生成uuid
def ut_xml_uuid(xml_file_path):
    if xml_file_path == '':
        tkinter.messagebox.showinfo(title='注意',message='请选择正确的VC配置文件')
        return
    # 更改编码格式-utf-8
    file_backup(xml_file_path)
    xml_file = open(xml_file_path, 'r')
    text = xml_file.read()
    text = text.replace(u'encoding="gb2312"', u'encoding="utf-8"')
    dom = Dom.parseString(text.encode('utf-8'))
    #生成uuid

    for filter_node in dom.getElementsByTagName('Filter'):
            str_uuid=str(uuid.uuid1())
            filter_node.setAttribute('UniqueIdentifier',str_uuid)
    #存储
    xml_file=open(xml_file_path,'w')
    dom.writexml(xml_file, indent='\t', newl='\n',encoding='utf-8')

    #更改编码格式-gb2312
    xml_file=open(xml_file_path,'r')
    text = xml_file.read()
    text = text.replace(u'encoding="utf-8"', u'encoding="gb2312"')
    xml_file = open(xml_file_path, 'w')
    xml_file.write(text)
    xml_file.close()
    tkinter.messagebox.showinfo(title='注意', message='UUID生成完成')

#编译为C++代码
def ut_xml_change_compile_cpp(xml_file_path):
    if xml_file_path == '':
        tkinter.messagebox.showinfo(title='注意', message='请选择正确的VC配置文件')
        return
    # 更改编码格式-utf-8
    file_backup(xml_file_path)
    xml_file = open(xml_file_path, 'r')
    text = xml_file.read()
    text = text.replace(u'encoding="gb2312"', u'encoding="utf-8"')
    dom = Dom.parseString(text.encode('utf-8'))
    #
    for h_node in dom.getElementsByTagName('File'):
        h_file = h_node.getAttribute('RelativePath')
        if os.path.splitext(h_file)[1] in ['.c','.cpp']:
            file_conf_node=dom.createElement('FileConfiguration')
            file_conf_node.setAttribute('Name','Debug|Win32')
            h_node.appendChild(file_conf_node)
            file_conf_tool_node=dom.createElement('Tool')
            file_conf_tool_node.setAttribute('Name','VCCLCompilerTool')
            file_conf_tool_node.setAttribute('CompileAs','2')
            file_conf_node.appendChild(file_conf_tool_node)

    # 存储
    xml_file = open(xml_file_path, 'w')
    dom.writexml(xml_file, indent='\t', newl='\n', encoding='utf-8')

    # 更改编码格式-gb2312
    xml_file = open(xml_file_path, 'r')
    text = xml_file.read()
    text = text.replace(u'encoding="utf-8"', u'encoding="gb2312"')
    xml_file = open(xml_file_path, 'w')
    xml_file.write(text)
    xml_file.close()
    tkinter.messagebox.showinfo(title='注意', message=u'所有C文件属性已更改为“编译为C++代码”')

# tk获取文件路径
def select_file_path(file_path):
    file_path.set(askopenfilename())
# tk获取文件夹路径
def select_folder_path(folder_path):
    folder_path.set(askdirectory())
# 创建顶层界面
tkRoot.title('VC工程搭建小工具')
xmlFilePath=StringVar()
codeFolderPath=StringVar()
uniq_uuid=StringVar()
dir_info = tkinter.Entry(tkRoot, textvariable=xmlFilePath)
dir_info.grid(row=2, column=0, sticky="we")
tkinter.Button(tkRoot, text=".vcproj文件", command=lambda: select_file_path(xmlFilePath), width=10).grid(row=2, column=1, padx=5)

dir_info = tkinter.Entry(tkRoot, textvariable=codeFolderPath)
dir_info.grid(row=3, column=0, sticky="we")
tkinter.Button(tkRoot, text="代码目录", command=lambda: select_folder_path(codeFolderPath), width=10).grid(row=3, column=1, padx=5)

dir_info = tkinter.Entry(tkRoot, textvariable=uniq_uuid)
dir_info.grid(row=4, column=0, sticky="we")
dir_info = tkinter.Label(tkRoot,text='VC筛选器UUID')
dir_info.grid(row=4, column=1, sticky="we")

tkinter.Button(tkRoot, text="生成UUID", command=lambda: ut_xml_uuid(xmlFilePath.get()), bg='white').grid(row=5, column=1, columnspan=1, padx=5, pady=5, sticky="we")
tkinter.Button(tkRoot, text="批量导入", command=lambda: ut_xml_init(xmlFilePath.get(),codeFolderPath.get(),uniq_uuid.get()), bg='pink').grid(row=5, column=0, columnspan=1, padx=5, pady=5, sticky="we")
tkinter.Button(tkRoot, text="刷新文件&修复引用", command=lambda: ut_xml_add_include(xmlFilePath.get()), bg='pink').grid(row=6, column=0, columnspan=2, padx=5, pady=5, sticky="we")
tkinter.Button(tkRoot, text=u"采用“C++代码编译”", command=lambda: ut_xml_change_compile_cpp(xmlFilePath.get()), bg='pink').grid(row=7, column=0, columnspan=2, padx=5, pady=5, sticky="we")
tkRoot.mainloop()
