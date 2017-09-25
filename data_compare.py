#coding=utf-8
import os
import sys
import tkinter
import tkinter.messagebox
from tkinter import ttk
from tkinter.filedialog import *
import shutil
from tkinter.filedialog import *
import win32api
import ctypes
import psutil
tkRoot=tkinter.Tk()
proc_dict=dict()
#数据类型变化
def data_reshape(out_len_str, in_offset_str, in_len_str, byte_num_str, ahp_type_str, rearrange,num_list):
    real_num_len=len(num_list[0])
    #字节数转换
    try:
        byte_num=int(byte_num_str[0])
        num_len=byte_num*2
        if real_num_len>num_len:
            if divmod(real_num_len,num_len)[1]!=0:
                tkinter.messagebox.showinfo(title='注意', message='数据字节数异常')
                return
            re_num_list=list()
            rep_time=divmod(real_num_len,num_len)[0]
            for i in range(len(num_list)):
                for j in range(rep_time):
                    re_num_list.append(num_list[i][real_num_len-(j+1)*num_len:real_num_len-j*num_len])
            num_list=re_num_list
        elif real_num_len<num_len:
            if divmod(num_len,real_num_len)[1]!=0:
                tkinter.messagebox.showinfo(title='注意', message='数据字节数异常')
                return
            re_num_list=list()
            rep_time=divmod(num_len,real_num_len)[0]
            for i in range(divmod(len(num_list),rep_time)[0]):
                re_num_list.append('')
                for j in range(rep_time):
                    re_num_list[i]=num_list[i*rep_time+j]+re_num_list[i]
            num_list=re_num_list
    except:
        a=0
    #截取
    out_num_list=list()
    try:
        out_len = int(out_len_str)
        in_offset = int(in_offset_str)
        in_len = int(in_len_str)
        in_end = in_offset + in_len
        if rearrange==0:
            rep_time=divmod(len(num_list),out_len)[0]
            for i in range(rep_time):
                out_num_list.extend(num_list[i*out_len+in_offset:i*out_len+in_end])
        else:
            rep_time = divmod(len(num_list), out_len)[0]
            inter_rep_time = divmod(out_len, in_len)[0]
            for j in range(inter_rep_time):
                for i in range(rep_time):
                    out_num_list.extend(num_list[i * out_len + in_offset+j*in_len:i * out_len+j*in_len + in_end])
    except:
        out_num_list=num_list
    #输出
    out_str=''
    file = open('C:/MEM_OUT.txt', 'w', encoding='utf-8')
    if ahp_type_str=='大写':
        for item in out_num_list:
            out_str=out_str+'0x'+item.upper()+'\n'
    else:
        for item in out_num_list:
            out_str=out_str+'0x'+item.lower()+'\n'
    out_str = out_str[:len(out_str) - 1]
    file.write(out_str)
    file.close()
    tkRoot.clipboard_clear()
    tkRoot.clipboard_append(out_str)

#数据提取
def data_extract(out_len_str, in_offset_str, in_len_str, byte_num_str, ahp_type_str, rearrange):
    result=tkRoot.clipboard_get()
    file_real_data=str(result)
    file_real_data=re.sub(r'^\s*','',file_real_data)
    file_real_data = re.sub(r'[\da-fA-FxX]+\s*[:：]+\s*', '', file_real_data)
    oral_list = re.split(r'[\s:：,，;；]+', file_real_data)
    num_list = list()
    if len(oral_list) <=1:
        tkinter.messagebox.showinfo(title='注意',message='无数据')
        return
    real_num_len = len(oral_list[1])
    #读取数据
    for item in oral_list:
        if re.match(r'[\da-fA-FxX]+', item) != None and len(item) == real_num_len :
            if item[0:2]=='0x'or item[0:2]=='0X':
                item = item[2:]
            num_list.append(item)
    data_reshape(out_len_str, in_offset_str, in_len_str, byte_num_str, ahp_type_str, rearrange,num_list)

#读取内存
def men_read(mem_address,mem_length):
    refresh_select_list()
    byte_num=int(byte_type.get()[0])
    real_len=divmod(mem_length*byte_num,4)[0]
    PROCESS_ALL_ACCESS = (0x000F0000 | 0x00100000 | 0xFFF)
    pid=proc_dict[thread_type.get()]
    phand = win32api.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    date = ctypes.c_ulong()
    try:
        mydll = ctypes.windll.LoadLibrary("C:\Windows\System32\kernel32.dll")
    except:
        tkinter.messagebox.showinfo(title='注意', message='C:\Windows\System32\kernel32.dll丢失')
        return
    num_list=list()
    try:
        for i in range(real_len):
            mydll.ReadProcessMemory(int(phand), mem_address+4*i, ctypes.byref(date),4, None)
            hex_num=hex(date.value)
            hex_num=hex_num[2:].zfill(8)
            num_list.append(hex_num)
        data_reshape(out_len.get(), in_offset.get(), in_len.get(), byte_type.get(), ahp_type.get(), check_var.get(),num_list)
    except:
        tkinter.messagebox.showinfo(title='注意', message='内存读取异常')
    return

#刷新窗口列表
def refresh_select_list(*args):
    proc_dict.clear()
    for proc in psutil.process_iter():
        proc_name=proc.name()
        proc_id=proc.pid
        if proc_dict.get(proc_name)==None:
            proc_dict[proc_name]=proc_id
        else:
            i=1
            while proc_dict.get(proc_name+str(i))!=None:
                i=i+1
            proc_dict[proc_name+str(i)]=proc_id
    window_name_list=list(proc_dict)
    window_name_list.sort()
    window_name_list.insert(0,'剪切板')
    proc_select_lis['values']=window_name_list
#切换模式
def proc_select_event(*args):
    if thread_type.get()!='剪切板':
        mem_addr_entry['state']='normal'
        mem_len_entry['state']='normal'
        main_butt['text'] = '内存读取'
        main_butt['command'] = lambda:men_read(mem_addr.get(),mem_len.get())
    else:
        mem_addr_entry['state'] = 'disabled'
        mem_len_entry['state'] = 'disabled'
        main_butt['text']='数据格式转换'
        main_butt['command']=lambda: data_extract(out_len.get(), in_offset.get(), in_len.get(), byte_type.get(), ahp_type.get(), check_var.get())
#清空参数
def clear_para(out_len, in_offset, in_len):
    out_len.set('')
    in_offset.set('')
    in_len.set('')

#二维搬移UI变化
def DDdemap():
    if check_var.get()==0:
        offset_entry['state']='normal'
        sub_part_log['text']='段内子段长度'
    else:
        offset_entry['state'] = 'disabled'
        sub_part_log['text'] = '段内分段长度'
        in_len.set('')
#自动读取beyond compare配置
def ini_beyondcompare():
    if os.path.isfile('data_compare.ini'):
        file_ini=open('data_compare.ini','r',encoding='utf-8')
        path_ini=file_ini.readline()
        file_ini.close()
        if path_ini!='':
            bc_path.set(path_ini)
            return 0
    bc_path.set('无')
    return -1

#手动配置beyond compare
def set_beyondcompare():
    bc_path.set(askopenfilename(title='选择Beyond Compare.exe',filetypes = [('exe','EXE')]))
    file_ini = open('data_compare.ini', 'w', encoding='utf-8')
    if bc_path.get()!='':
        file_ini.write(bc_path.get())
    else:
        bc_path.set('无')
    file_ini.close()
    bc_butt['state']='normal'

#启动beyond compare
def do_beyondcompare():
    com_file_path=askopenfilename(title='选择对比数据文件')
    chdir,exe=os.path.split(bc_path.get())
    os.chdir(chdir)
    try:
        os.system(exe+' -b '+'C:/MEM_OUT.txt '+com_file_path)
    except:
        tkinter.messagebox.showinfo(title='注意', message='Beyond Compare异常,请重新配置')
        bc_butt['state']='disabled'
        bc_path.set('无')

out_len=StringVar()
in_offset=StringVar()
in_len=StringVar()
byte_type=StringVar()
ahp_type=StringVar()
thread_type=StringVar()
check_var=IntVar()
mem_addr=IntVar()
mem_len=IntVar()
bc_path=StringVar()
row_num=0
tkRoot.title('数据比对工具')
tkinter.Label(tkRoot,text='结果在C:\MEM_OUT.txt和剪切板中,以下非必填',background='green').grid(row=row_num,columnspan=4,sticky="we")
row_num=row_num+1
#分段参数
tkinter.Label(tkRoot,text='数据分段长度').grid(row=1, column=0, sticky="nw",pady=7)
tkinter.Entry(tkRoot, textvariable=out_len,width=10).grid(row=1, column=1, sticky="nw",pady=7)
tkinter.Label(tkRoot,text='段内偏移').grid(row=1, column=2, sticky="n",pady=7,padx=10)
offset_entry=tkinter.Entry(tkRoot, textvariable=in_offset,width=10)
offset_entry.grid(row=1, column=3, sticky="nw",pady=7)
sub_part_log=tkinter.Label(tkRoot, text='段内有效长度')
sub_part_log.grid(row=2, column=0, sticky="nw")
tkinter.Entry(tkRoot, textvariable=in_len,width=10).grid(row=2, column=1, sticky="nw")
#重置参数
clear_butt=tkinter.Button(tkRoot, text="参数清空", command=lambda: clear_para(out_len, in_offset, in_len), height=1,width=10)
clear_butt.grid(row=2, column=2, columnspan=2 , sticky="n")
#字节数
byte_select_lis=ttk.Combobox(tkRoot, textvariable=byte_type, state='readonly', values=('8字节','4字节', '2字节','1字节'), width=7)
byte_select_lis.current(1)
byte_select_lis.grid(row=3, column=0, sticky="n",pady=7)
#大小写
alph_select_lis=ttk.Combobox(tkRoot,textvariable=ahp_type,state='readonly',values=('大写','小写'),width=7)
alph_select_lis.current(0)
alph_select_lis.grid(row=3, column=1, sticky="n",pady=7)
#二维搬移
check_circle=Checkbutton(tkRoot, text="二维搬移", variable=check_var,command=DDdemap)
check_circle.deselect()
check_circle.grid(row=3, column=2,columnspan=2, sticky="n",pady=7)
#选择程序
tkinter.Label(tkRoot,text='数据源').grid(row=4, column=0, sticky="n")
proc_select_lis=ttk.Combobox(tkRoot, textvariable=thread_type, values=('剪切板'),state='readonly',width=25)
proc_select_lis.current(0)
proc_select_lis.bind('<Button-1>',refresh_select_list)
proc_select_lis.bind('<<ComboboxSelected>>',proc_select_event)
proc_select_lis.grid(row=4, column=1, columnspan=3, sticky="nw")
#tkinter.Button(tkRoot, text="刷新程序", command=refresh_select_list,background='orange').grid(row=4, column=3, sticky="n")
#内存地址
tkinter.Label(tkRoot,text='内存地址').grid(row=5, column=0, sticky="n",pady=5)
mem_addr_entry=tkinter.Entry(tkRoot, textvariable=mem_addr,state = 'disabled',width=10)
mem_addr_entry.grid(row=5, column=1, sticky="nw",pady=5)
tkinter.Label(tkRoot,text='数据长度').grid(row=5, column=2, sticky="n",pady=5)
mem_len_entry=tkinter.Entry(tkRoot, textvariable=mem_len,state = 'disabled',width=10)
mem_len_entry.grid(row=5, column=3, sticky="nw",pady=5)
main_butt=tkinter.Button(tkRoot, text="数据格式转换", command=lambda: data_extract(out_len.get(), in_offset.get(), in_len.get(), byte_type.get(), ahp_type.get(), check_var.get()), height=2, bg='orange')
main_butt.grid(row=6, column=0, columnspan=4, padx=5, pady=5, sticky="we")
if ini_beyondcompare()==0:
    bc_state='normal'
else:
    bc_state='disabled'
set_butt=tkinter.Button(tkRoot, text='BC路径', height=1,command=set_beyondcompare)
set_butt.grid(row=7, column=0,  padx=5, sticky="we")
bc_path_entry=tkinter.Entry(tkRoot, textvariable=bc_path,state = 'readonly')
bc_path_entry.grid(row=7, column=1,columnspan=2, sticky="we")
bc_butt=tkinter.Button(tkRoot, text="BCompare", height=1, bg='orange',state=bc_state,command=do_beyondcompare)
bc_butt.grid(row=7, column=3, columnspan=1, padx=5, pady=5, sticky="we")

tkRoot.mainloop()
