#!/usr/bin/env bash
# =============================================================================
# 一键安装 Samba 并共享整个根目录（/） - 极度危险！仅限测试/隔离环境
# 使用方式：sudo bash 此脚本
# 作者提醒：共享 / 极不安全，生产环境禁止！建议只共享子目录。
# =============================================================================

set -euo pipefail

# ──────────────────────────────────────────────────────────────────────────────
# 检查是否 root 执行
# ──────────────────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo "错误：请使用 sudo 执行此脚本" >&2
    exit 1
fi

echo "┌────────────────────────────────────────────────────────────┐"
echo "│          Samba 一键安装 - 共享整个根目录（/）              │"
echo "│                                                            │"
echo "│ 警告：此操作极度危险！会暴露整个系统文件给网络！          │"
echo "│ 只在隔离测试环境使用，生产/公网环境绝对禁止！             │"
echo "│ 继续执行请输入 YES（大写）                                 │"
echo "└────────────────────────────────────────────────────────────┘"

read -r confirm
if [[ "$confirm" != "YES" ]]; then
    echo "已取消操作。"
    exit 0
fi

# ──────────────────────────────────────────────────────────────────────────────
# 1. 更新系统 & 安装 Samba
# ──────────────────────────────────────────────────────────────────────────────
echo "正在更新系统并安装 Samba..."
apt update -y
apt upgrade -y
apt install samba samba-common-bin -y

# ──────────────────────────────────────────────────────────────────────────────
# 2. 备份原配置
# ──────────────────────────────────────────────────────────────────────────────
SMB_CONF="/etc/samba/smb.conf"
BACKUP="${SMB_CONF}.bak.$(date +%Y%m%d_%H%M%S)"
cp -p "$SMB_CONF" "$BACKUP"
echo "已备份原配置：$BACKUP"

# ──────────────────────────────────────────────────────────────────────────────
# 3. 清空原有 shares 并添加根目录共享
# ──────────────────────────────────────────────────────────────────────────────
# 先保留 [global] 部分，然后追加新配置
sed -i '/^\[.*\]/,/^$/d' "$SMB_CONF"  # 删除所有 [share] 段（小心！）

cat >> "$SMB_CONF" << 'EOF'

[global]
    workgroup = WORKGROUP
    server string = Linux Root Share (DANGER ZONE)
    netbios name = ROOTSERVER
    security = user
    map to guest = never
    dns proxy = no
    min protocol = SMB2_10
    smb encrypt = desired

# ────────────── 共享整个根目录 ──────────────
[rootshare]
    comment = Entire Root Filesystem - EXTREME DANGER
    path = /
    browseable = yes
    read only = no
    writable = yes
    guest ok = no                   # 必须密码登录，禁止匿名
    valid users = root, @sudo       # 只允许 root 和 sudo 组用户
    force user = root
    force group = root
    create mask = 0755
    directory mask = 0755
    follow symlinks = yes
    wide links = yes                # 允许跨文件系统链接（危险但必要）

EOF

# ──────────────────────────────────────────────────────────────────────────────
# 4. 添加 Samba 用户（root）
# ──────────────────────────────────────────────────────────────────────────────
echo "为 root 添加 Samba 密码（请设置一个强密码，与 Linux root 密码可不同）"
smbpasswd -a root
smbpasswd -e root

echo ""
echo "可选：如果你想用普通用户访问（推荐比直接用 root 安全一点）"
read -p "要创建专用 Samba 用户吗？(y/n): " create_user
if [[ "$create_user" =~ ^[Yy]$ ]]; then
    read -p "请输入新用户名: " smbuser
    useradd -M -s /bin/false "$smbuser"
    passwd "$smbuser"
    smbpasswd -a "$smbuser"
    smbpasswd -e "$smbuser"
    usermod -aG sudo "$smbuser"   # 加到 sudo 组以有较高权限
    echo "已添加用户 $smbuser，可用它登录 Samba"
fi

# ──────────────────────────────────────────────────────────────────────────────
# 5. 测试配置 & 重启服务
# ──────────────────────────────────────────────────────────────────────────────
echo "测试 Samba 配置..."
testparm -s

echo "重启 Samba 服务..."
systemctl restart smbd nmbd
systemctl enable smbd nmbd

# 防火墙（如果使用 ufw）
if command -v ufw >/dev/null; then
    ufw allow samba
    ufw reload
fi

# ──────────────────────────────────────────────────────────────────────────────
# 完成提示
# ──────────────────────────────────────────────────────────────────────────────
cat << EOF


┌────────────────────────────────────────────────────────────┐
│                     配置完成！                             │
├────────────────────────────────────────────────────────────┤
│ 访问方式（Windows / Mac）：                                │
│   文件资源管理器 / Finder → \\$(hostname -I | awk '{print $1}') 或 \\\\$(hostname) │
│   用户名：root（或你创建的 smbuser）                       │
│   密码：你刚才设置的 Samba 密码                           │
│                                                            │
│ 再次警告：共享 / 非常危险！建议立即：                      │
│ 1. 只在内网使用，绝不暴露 445 端口到公网                  │
│ 2. 使用完后删除 [rootshare] 段并重启 smbd                  │
│ 3. 考虑改用 SFTP/SSHFS 或只共享子目录                      │
└────────────────────────────────────────────────────────────┘
EOF

exit 0
