# Android 客户端

这是基于 Capacitor 的网页客户端，默认连接 capacitor.config.json 中的 server.url。连接自己的服务时，请修改该地址。

在 mobile-app 目录执行：

```bash
npm ci
npx cap sync android
npx cap open android
```

随后在 Android Studio 中配置 Android SDK 并构建。node_modules、Gradle 缓存、构建产物、签名文件和本机 SDK 路径不提交。当前仅提供源码，本次仓库更新未验证 Android 构建。
