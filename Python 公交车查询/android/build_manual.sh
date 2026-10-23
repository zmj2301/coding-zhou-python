#!/usr/bin/env bash
# 湘潭实时公交 —— 手工打包 APK（不依赖 Gradle）
# 流程: aapt2 编译资源 -> javac -> d8 转 dex -> jar 合并 -> zipalign -> apksigner
#
# 注意：项目路径含中文/空格时，Java 工具(apksigner/aapt2)会因 GBK 解码失败报
#      FileNotFoundException，故最后几步在纯英文暂存目录执行。
set -e
cd "$(dirname "$0")"

export JAVA_HOME="/e/jdk17/jdk-17.0.2"
export PATH="$JAVA_HOME/bin:$PATH"

SDK=/e/android-sdk
BT=$SDK/build-tools/34.0.0
PLATFORM=$SDK/platforms/android-34/android.jar
APP=app/src/main
PKG=com.workbuddy.xiangtanbus
WORK=/e/xtb-stage/work
STAGE=/e/xtb-stage
KS=$STAGE/debug.keystore
PYPY="C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe"

VERSION=$(grep -o 'APP_VERSION = "[^"]*"' $PWD/$APP/java/$PKG/ChelaileClient.java 2>/dev/null | sed 's/.*"\(.*\)"/\1/')
[ -z "$VERSION" ] && VERSION="1.1.0"
APK_NAME="xiangtan-bus-v$VERSION.apk"

echo "========================================"
echo " 湘潭实时公交 v${VERSION}  手工打包"
echo "========================================"

# 用 Python 完成清理与拷贝（Git Bash 的 rm 在 Windows 盘符路径下行为不可靠）
"$PYPY" - "$STAGE" "$PWD" "$APP" <<'PYEOF2'
import os, shutil, sys
stage, proj, app = sys.argv[1], sys.argv[2], os.path.join(sys.argv[2], sys.argv[3])
shutil.rmtree(stage, ignore_errors=True)
work = os.path.join(stage, "work")
for d in ["res", "classes", "dex", "apk"]:
    os.makedirs(os.path.join(work, d), exist_ok=True)
os.makedirs(os.path.join(stage, "src"), exist_ok=True)
shutil.copy(os.path.join(proj, "debug.keystore"), os.path.join(stage, "debug.keystore"))
shutil.copy(os.path.join(app, "AndroidManifest.xml"), os.path.join(stage, "AndroidManifest.xml"))
shutil.copytree(os.path.join(app, "java"), os.path.join(stage, "src"), dirs_exist_ok=True)
shutil.copytree(os.path.join(app, "res"), os.path.join(work, "res"), dirs_exist_ok=True)
print("staging ready")
PYEOF2

echo "[1/6] aapt2 编译资源 ..."
$BT/aapt2.exe compile --dir $WORK/res -o $WORK/res.zip

echo "[2/6] aapt2 链接 ..."
$BT/aapt2.exe link -o $WORK/base.apk \
  -I $PLATFORM \
  --manifest $STAGE/AndroidManifest.xml \
  -R $WORK/res.zip \
  --java $WORK/gen \
  --min-sdk-version 24 \
  --target-sdk-version 34 \
  --version-code 2 \
  --version-name "$VERSION" \
  --auto-add-overlay

echo "[3/6] javac 编译 Java ..."
"$PYPY" -c "import glob,sys; fs=glob.glob(sys.argv[2]+'/**/*.java',recursive=True)+glob.glob(sys.argv[3]+'/**/*.java',recursive=True); open(sys.argv[1],'w',newline='\\n').write('\\n'.join(f.replace('/e/','E:/').replace('/','\\\\') for f in fs))" "$WORK/sources.txt" "$WORK/gen" "$STAGE/src"
WIN_SOURCES=$(echo $WORK/sources.txt | sed 's|^/e/|E:/|')
$JAVA_HOME/bin/javac -encoding UTF-8 -nowarn \
  -source 17 -target 17 \
  -classpath $PLATFORM \
  -d $WORK/classes \
  @"$WIN_SOURCES"

echo "[4/6] d8 转 DEX ..."
"$PYPY" -c "import glob,sys; fs=glob.glob(sys.argv[2]+'/**/*.class',recursive=True); open(sys.argv[1],'w',newline='\\n').write('\\n'.join(f.replace('/e/','E:/').replace('/','\\\\') for f in fs))" "$WORK/classes.txt" "$WORK/classes"
WIN_CLASSES=$(echo $WORK/classes.txt | sed 's|^/e/|E:/|')
cmd //c "E:/android-sdk/build-tools/34.0.0/d8.bat" --lib $PLATFORM --min-api 24 --output $WORK/dex @"$WIN_CLASSES"

echo "[5/6] 合并资源与 DEX ..."
unzip -q -o $WORK/base.apk -d $WORK/apk
cp $WORK/dex/classes.dex $WORK/apk/
# Android 10+ 要求 resources.arsc 不压缩且 4 字节对齐，用 Python zipfile 精确控制
"$PYPY" -c "import os,sys,zipfile; src,dst,store=sys.argv[1],sys.argv[2],{'resources.arsc','AndroidManifest.xml'}; z=zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f),src).replace(os.sep,'/'), zipfile.ZIP_STORED if f in store else zipfile.ZIP_DEFLATED) for r,_,fs in os.walk(src) for f in fs]; z.close()" "$WORK/apk" "$STAGE/unsigned.apk"

echo "[6/6] 对齐并签名（英文暂存目录）..."
$BT/zipalign.exe -f 4 $STAGE/unsigned.apk $STAGE/aligned.apk
cmd //c "E:/android-sdk/build-tools/34.0.0/apksigner.bat" sign \
  --ks $STAGE/debug.keystore \
  --ks-pass pass:android \
  --key-pass pass:android \
  --ks-key-alias androiddebugkey \
  --out $STAGE/$APK_NAME \
  $STAGE/aligned.apk

cmd //c "E:/android-sdk/build-tools/34.0.0/apksigner.bat" verify $STAGE/$APK_NAME

"$PYPY" -c "import os,shutil,sys; d=os.path.join(sys.argv[1],'bin'); os.makedirs(d,exist_ok=True); shutil.copy(os.path.join(sys.argv[2],sys.argv[3]), os.path.join(d,sys.argv[3]))" "$PWD" "$STAGE" "$APK_NAME"

echo ""
echo "========================================"
ls -la "$PWD/bin/$APK_NAME"
echo "签名校验通过，可直接安装到 MuMu 模拟器"
echo "构建完成 v${VERSION}"
