# 简介
该脚本用于生成 `java webapp` 两个版本之间的差异文件，也就是俗称的 patch。它的主要工作流程如下：

1. 从指定的 subversion 仓库拉取两个版本的源代码
2. 使用 maven 分别构建这两个版本
3. 比较两个版本的构建物，并生成差异文件

# 执行前提

### python 版本
该脚本必须要 `python 3.5` 以上版本方可执行。

### 依赖程序
由于该脚本需要通过 subprocess 执行 subversion 和 maven 程序，因此在运行脚本前，需要确保已经安装了 subversion
客户端及 maven，并且确保在命令行下可以执行 svn 和 mvn。

# 执行步骤

### 配置文件

```javascript
{

  "workspace": {
    "path": "C:/Users/watertao/Desktop/workspace"  // 工作目录
  },

  "approaches": [

    {
      "processor": "VCSProcessor",
      "ignore": true,
      "configuration": {
        "working_copies": [
          // 设置 SVN 的地址，以及本地的保存目录，每次在执行脚本之前，需要指定是构建哪两个版本的程序
          { "path": "conf/maven", "url": "http://10.10.10.176:88/svn/accountcenter/Devconf/maven" },  // maven 的 配置，此处一般不做修改
          { "path": "base/common", "url": "http://10.10.10.176:88/svn/accountcenter/Code/accountcenter/branches/2.9.7.4/common" },  // 基线版本（上一个发布版本）的SVN地址
          { "path": "base/suss", "url": "http://10.10.10.176:88/svn/accountcenter/Code/accountcenter/branches/2.9.7.4/suss" }, // 基线版本（上一个发布版本）的SVN地址
          { "path": "dest/common", "url": "http://10.10.10.176:88/svn/accountcenter/Code/accountcenter/branches/2.9.7.5/common" },  // 目标版本（本次需要发布的版本）的SVN地址
          { "path": "dest/suss", "url": "http://10.10.10.176:88/svn/accountcenter/Code/accountcenter/branches/2.9.7.5/suss" }  // 目标版本（本次需要发布的版本）的SVN地址
        ]
      }
    },

    {
      "processor": "BUILDProcessor",
      "ignore": true,
      "configuration": {
        "mvn_setting": "conf/maven/settings.xml",
        "builds": [
          // 构建，按顺序执行
          { "lp": "clean install -Dmaven.test.skip=true", "path": "base/common" },
          { "lp": "clean install -Dmaven.test.skip=true", "path": "base/suss" },
          { "lp": "clean install -Dmaven.test.skip=true", "path": "dest/common" },
          { "lp": "clean install -Dmaven.test.skip=true", "path": "dest/suss" }
        ]
      }
    },

    {
      "processor": "PATCHProcessor",
      "ignore": true,
      "configuration": {
        // 指定需要比对差异的目录
        "base_path": "base/suss/securities-bp-suss/target/securities-bp-suss-0.0.1-SNAPSHOT",
        "dest_path": "dest/suss/securities-bp-suss/target/securities-bp-suss-0.0.1-SNAPSHOT",
        "output_path": "output/suss",
        "patchfile_path": "output/patch.txt"
      }
    }

  ]

}
```   

配置文件中大部分参数都可以不做修改，用缺省的配置即可。 其中比较重要的有两处：

- VCSProcessor 中的 working_copies
这里需要指定基线版本的代码 SVN 地址 和 目标版本的代码 SVN 地址， 因为我们需要比对这两个版本之间的差异，最终得出一个差分包，在上面的范例中， 基线版本取的是 2.9.7.4,
目标版本是 2.9.7.5，如果构建涉及到多个模块（如 上例中的 common 和 suss），则需要设定多个配置项。

- PATCHProcessor 中的 base_path 和 dest_path
构建完成之后，在target目录中会包含构建后的包，我们需要指定地址，方便脚本做两个目录的比对

### 执行

```
python cmp.py suss
```

其中参数 suss 告知脚本去找同级目录下的 suss.json 配置文件。
