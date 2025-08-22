# セルフホステッドランナーセットアップガイド (VNet環境)

このガイドでは、Azure VNet内でGitHub Actionsセルフホステッドランナーをセットアップし、プライベートエンドポイント経由でACRにアクセスする方法を説明します。

## 前提条件

- Azure VMとACRが同じVNet内に存在する
- ACRにプライベートエンドポイントが設定されている
- VMからACRへの内部接続が確立されている
- VM OSがRHEL 9/CentOS Stream 9（このガイドはRHEL系を想定）

## 1. 既存のVNet内VMへの接続

```bash
# VMにSSH接続（公開IPまたはBastion経由）
ssh -i <your-key.pem> <username>@<VM-PUBLIC-IP>
# 例: ssh -i myKey.pem tech0admin@20.243.169.166
```

## 2. 必要なソフトウェアのインストール

### Ubuntu/Debian系の場合

```bash
# システムを更新
sudo apt update && sudo apt upgrade -y

# Dockerのインストール
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker

# Docker動作確認
docker --version
```

### Red Hat/CentOS/RHEL系の場合

#### RHEL 8/CentOS 8以前

```bash
# システムを更新
sudo yum update -y

# Dockerのインストール
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# Dockerサービスの開始
sudo systemctl enable docker
sudo systemctl start docker

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker

# Docker動作確認
docker --version
```

#### RHEL 9/CentOS Stream 9の場合（Podman-dockerを使用）

```bash
# システムを更新
sudo dnf update -y

# Podmanのインストール
sudo dnf install -y podman

# Podmanソケットの有効化
sudo systemctl enable --now podman.socket

# podman-dockerのインストール（dockerコマンドの互換性のため）
sudo dnf install -y podman-docker

# 動作確認
podman --version
# 期待される出力例: podman version 4.9.4-rhel

# コンテナランタイムのテスト
podman run hello-world

# dockerコマンドの確認（podmanへのシンボリックリンク）
docker --version
```

#### 代替方法：Docker CEを手動でインストール（RHEL 9）

```bash
# 必要なパッケージのインストール
sudo dnf install -y dnf-plugins-core

# Docker CE用のリポジトリを追加（CentOS 8用を使用）
sudo dnf config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# リポジトリの調整
sudo sed -i 's/\$releasever/8/g' /etc/yum.repos.d/docker-ce.repo

# Dockerのインストール
sudo dnf install -y docker-ce docker-ce-cli containerd.io --allowerasing

# Dockerサービスの開始
sudo systemctl enable docker
sudo systemctl start docker

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER
newgrp docker
```

## 3. 追加の設定（RHEL 9/Podmanの場合）

GitHub ActionsランナーがPodmanを使用できるように追加設定：

```bash
# rootlessモードでの実行を許可
sudo sysctl -w kernel.unprivileged_userns_clone=1
echo "kernel.unprivileged_userns_clone=1" | sudo tee -a /etc/sysctl.conf

# SELinuxコンテキストの設定（必要に応じて）
sudo setsebool -P container_manage_cgroup on

# ユーザーのサブUID/GIDの設定確認
grep $USER /etc/subuid /etc/subgid
```

## 4. ディスク容量の確認とインストール場所の選択

```bash
# ディスク容量を確認
df -h

# 十分な容量（2GB以上推奨）がある場所を選択
# 例: /homeが小さい場合は/mntを使用
```

## 5. GitHub Actionsランナーのインストール

```bash
# 容量に余裕のあるディレクトリを使用（例: /mnt）
sudo mkdir -p /mnt/github-runner
sudo chown $USER:$USER /mnt/github-runner
cd /mnt/github-runner

# 最新のランナーをダウンロード
curl -o actions-runner-linux-x64-2.328.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.328.0/actions-runner-linux-x64-2.328.0.tar.gz

# 解凍
tar xzf ./actions-runner-linux-x64-2.328.0.tar.gz
rm actions-runner-linux-x64-2.328.0.tar.gz
```

## 6. GitHubでランナートークンを取得

1. GitHubリポジトリにアクセス
2. **Settings** → **Actions** → **Runners** に移動
3. **New self-hosted runner** をクリック
4. 表示されるトークンをコピー

## 7. ランナーの設定

```bash
# ランナーを設定（対話形式）
./config.sh --url https://github.com/<GITHUB_USERNAME>/<REPOSITORY_NAME> --token <RUNNER_TOKEN>

# 設定時の入力例：
# - Runner group: [Enter for Default]
# - Runner name: azure-vnet-runner（または任意の名前）
# - Additional labels: rhel9,podman（カンマ区切り）
# - Work folder: [Enter for _work]
```

## 8. ランナーのテスト実行

```bash
# まず手動で動作確認
./run.sh

# 正常に「Listening for Jobs」と表示されたらCtrl+Cで停止
```

## 9. ランナーをサービスとして実行

```bash
# 実行権限を確認
chmod +x *.sh

# サービスのインストール（ユーザー指定）
sudo ./svc.sh install --user $USER

# サービスの開始
sudo systemctl start actions.runner.<ORG-REPO>.<RUNNER-NAME>.service

# サービスの状態確認
sudo systemctl status actions.runner.<ORG-REPO>.<RUNNER-NAME>.service

# ログの確認
sudo journalctl -u actions.runner.<ORG-REPO>.<RUNNER-NAME>.service -f
```

## 10. プライベートDNS解決の確認

VNet内でACRのプライベートエンドポイントを使用している場合：

```bash
# ACRのプライベートIPが解決されることを確認
nslookup <ACR_NAME>.azurecr.io

# 期待される結果：プライベートIPアドレス（10.x.x.x など）
```

## 11. ワークフローファイルの設定（Podman対応）

`.github/workflows/deploy-self-hosted.yml`:

```yaml
name: Build and Deploy via Self-Hosted Runner

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  build-and-deploy:
    runs-on: [self-hosted, linux, x64, azure-vnet, rhel9, podman]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Container Runtime Check
      run: |
        echo "Container runtime version:"
        podman --version || docker --version
    
    - name: Login to ACR
      run: |
        echo ${{ secrets.ACR_PASSWORD }} | podman login \
          ${{ secrets.ACR_LOGIN_SERVER }} \
          -u ${{ secrets.ACR_USERNAME }} \
          --password-stdin
    
    - name: Build and Push
      run: |
        # Podmanを使用（dockerコマンドはpodmanのエイリアス）
        podman build -t ${{ secrets.ACR_LOGIN_SERVER }}/${{ secrets.IMAGE_NAME }}:${{ github.sha }} .
        podman push ${{ secrets.ACR_LOGIN_SERVER }}/${{ secrets.IMAGE_NAME }}:${{ github.sha }}
```

## 必要なGitHub Secrets

リポジトリのSettings → Secrets and variablesで以下を設定：

- `ACR_LOGIN_SERVER`: <acr-name>.azurecr.io
- `ACR_USERNAME`: ACRのユーザー名
- `ACR_PASSWORD`: ACRのパスワード
- `IMAGE_NAME`: Dockerイメージ名

## トラブルシューティング

### ディスク容量不足の場合

```bash
# ディスク使用状況を確認
df -h

# 不要なファイルを削除
rm -rf ~/actions-runner  # 失敗したインストール
sudo dnf clean all       # パッケージキャッシュ
podman system prune -a -f # コンテナイメージ

# 別のディレクトリを使用（例: /mnt）
sudo mkdir -p /mnt/github-runner
sudo chown $USER:$USER /mnt/github-runner
```

### サービス起動エラーの場合

```bash
# 詳細なエラーログを確認
sudo journalctl -u actions.runner.* -n 100 --no-pager

# 権限を修正
chmod +x /mnt/github-runner/*.sh

# サービスを再インストール
sudo ./svc.sh uninstall
sudo ./svc.sh install --user $USER
sudo systemctl start actions.runner.*
```

### ランナーがオフラインの場合

```bash
# サービスの状態確認
sudo systemctl status actions.runner.*

# 手動実行でエラーを確認
cd /mnt/github-runner
./run.sh

# サービスの再起動
sudo systemctl restart actions.runner.*
```

### ACR接続エラーの場合

```bash
# DNS解決の確認
nslookup <ACR_NAME>.azurecr.io
dig +short <ACR_NAME>.azurecr.io

# プライベートエンドポイントへの接続確認
nc -zv <ACR_NAME>.azurecr.io 443

# Podmanでログインテスト
podman login <ACR_NAME>.azurecr.io -u <USERNAME> -p <PASSWORD>
```

### Podman特有の問題

```bash
# SELinuxが原因の場合
sudo setenforce 0  # 一時的に無効化（テスト用）

# Podmanソケットの確認
systemctl status podman.socket
sudo systemctl restart podman.socket

# rootlessモードの問題
podman info
```

## セキュリティベストプラクティス

1. **最小権限の原則**
   - ランナー専用のユーザーアカウントを作成
   - 必要最小限の権限のみ付与

2. **ネットワークセキュリティ**
   - VMのNSGで不要なポートを閉じる
   - VNet内通信のみに制限

3. **定期メンテナンス**
   - OSとDockerの定期更新
   - ランナーソフトウェアの更新

```bash
# 自動更新の設定
sudo apt install unattended-upgrades
sudo dpkg-reconfigure --priority=low unattended-upgrades
```

## 実際の実行例

```bash
# 1. SSH接続
ssh -i myKey.pem tech0admin@20.243.169.166

# 2. Podmanインストール
sudo dnf update -y
sudo dnf install -y podman
sudo systemctl enable --now podman.socket
sudo dnf install -y podman-docker

# 3. ディスク容量確認と場所選択
df -h
sudo mkdir -p /mnt/github-runner
sudo chown tech0admin:tech0admin /mnt/github-runner
cd /mnt/github-runner

# 4. ランナーインストール
curl -o actions-runner-linux-x64-2.328.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.328.0/actions-runner-linux-x64-2.328.0.tar.gz
tar xzf ./actions-runner-linux-x64-2.328.0.tar.gz
rm actions-runner-linux-x64-2.328.0.tar.gz

# 5. 設定（GitHubからトークン取得後）
./config.sh --url https://github.com/wkzhiro/security-api --token YOUR_TOKEN

# 6. テスト実行
./run.sh  # Ctrl+Cで停止

# 7. サービス化
sudo ./svc.sh install --user tech0admin
sudo systemctl start actions.runner.wkzhiro-security-api.vm-geek.service
sudo systemctl status actions.runner.wkzhiro-security-api.vm-geek.service
```

## ランナーの削除

必要に応じてランナーを削除する場合：

```bash
# サービスの停止と削除
sudo systemctl stop actions.runner.*
sudo ./svc.sh uninstall

# 設定の削除（GitHubから削除トークンを取得）
./config.sh remove --token <REMOVAL_TOKEN>

# ディレクトリの削除
cd ~
sudo rm -rf /mnt/github-runner
```