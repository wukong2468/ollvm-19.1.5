# ollvm 19.1.5

整合的ollvm

## 使用方法
- -mllvm -irobf # 强制开启混淆，用在希望给函数添加混淆注释的时候，如果开启了其它混淆那么这个指令就相当于多余的
- -mllvm -irobf-indbr # 开启间接跳转混淆并加密跳转目标
- -mllvm -level-indbr # 间接跳转混淆的加密层级，范围是0~3，0级表示不加密跳转目标
- -mllvm -irobf-icall # 开启间接函数调用混淆并加密目标函数地址
- -mllvm -level-icall # 间接函数调用混淆的加密层级，范围是0~3，0级表示不加密目标函数地址
- -mllvm -irobf-indgv # 开启间接全局变量混淆并加密变量地址
- -mllvm -level-indgv # 间接全局变量混淆的加密层级，范围是0~3，0级表示不加密变量地址
- -mllvm -irobf-fla # 开启控制流平坦化混淆
- -mllvm -irobf-sub # 开启指令替换混淆
- -mllvm -level-sub # 指令替换次数，范围是0~无限，0级表示替换1次
- -mllvm -irobf-bcf # 开启虚假控制流混淆
- -mllvm -level-bcf # 虚假控制流混淆概率，默认是80%，范围是0~100
- -mllvm -irobf-cse # 开启字符串混淆
- -mllvm -irobf-cie # 开启整数常量混淆并加密常量地址
- -mllvm -level-cie # 整数常量混淆的加密层级，范围是0~3，0级表示不加密常量地址
- -mllvm -irobf-cfe # 开启浮点数常量混淆并加密常量地址
- -mllvm -level-cfe # 浮点常量混淆的加密层级，范围是0~3，0级表示不加密常量地址
- -mllvm -irobf-config # 通过配置文件开启混淆，配置文件格式为json

## 使用示例

### 1. CMakeLists.txt文件
```
add_compile_options("SHELL:-mllvm -irobf-indbr")
add_compile_options("SHELL:-mllvm -level-indbr=2")
add_compile_options("SHELL:-mllvm -irobf-icall")
add_compile_options("SHELL:-mllvm -level-icall=2")
add_compile_options("SHELL:-mllvm -irobf-indgv")
add_compile_options("SHELL:-mllvm -level-indgv=2")
add_compile_options("SHELL:-mllvm -irobf-bcf")
add_compile_options("SHELL:-mllvm -level-bcf=40")
add_compile_options("SHELL:-mllvm -irobf-cse")
```

### 2. 配置文件
使用`-mllvm -irobf-config=path\to\config.json`参数设置混淆配置文件，文件内容如下
```
{
  "indbr": {
    "enable": true,
    "level": 3
  },
  "icall": {
    "enable": true,
    "level": 3
  },
  "indgv": {
    "enable": true,
    "level": 3
  },
}
```
### 3. 函数注释
`+indbr`表示开启混淆

`-indbr`表示关闭混淆

`^indbr=3`表示混淆层级设置为3
```
__attribute__((annotate("+indbr ^indbr=3 -icall ^indgv=2")))
int main() {
    std::cout << "HelloWorld" << std::endl;
    return 0;
}
```