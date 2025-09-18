# Complete Tutorial: GPG Keys for Debian Packaging

## 📋 Prerequisites
- Have an account at [mentors.debian.net](https://mentors.debian.net)
- Have `gpg` installed (comes by default in Debian)

---

## 1. **Create a GPG Key (if you don't have one)**

### Interactive Method:
```bash
gpg --full-generate-key
```
**Selections:**
- Key type: **1** (RSA and RSA)
- Key size: **4096**
- Validity: **2y** (2 years)
- Name and email: **Your full name and email**

### Automated Method (batch):
```bash
gpg --batch --generate-key <<EOF
%no-protection
Key-Type: RSA
Key-Length: 4096
Subkey-Type: RSA
Subkey-Length: 4096
Name-Real: Your Full Name
Name-Email: your-email@domain.com
Expire-Date: 2y
%commit
EOF
```

---

## 2. **Verify Existing Keys**

```bash
gpg --list-keys
```
**Expected output:**
```
pub   rsa4096 2024-01-01 [SC] [expires: 2026-01-01]
      0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
uid           [ultimate] Your Name <your-email@domain.com>
sub   rsa4096 2024-01-01 [E] [expires: 2026-01-01]
```

---

## 3. **Export Public Key in Required Format**

```bash
gpg --export --export-options export-minimal --armor 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

**Copy ALL the output** (including the `-----BEGIN` and `-----END` lines)

---

## 4. **Configure Key on mentors.debian.net**

1. Go to [mentors.debian.net](https://mentors.debian.net)
2. Log in
3. Go to your profile
4. Paste the complete key in "OpenGPG Key" field
5. Save changes

---

## 5. **Upload Key to Keyservers (recommended)**

```bash
gpg --send-keys 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

---

## 6. **Configure Environment for Packaging**

### Configure Git to use GPG:
```bash
git config --global user.signingkey 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
git config --global commit.gpgsign true
```

### Configure debuild to sign packages:
Ensure your `~/.devscripts` contains:
```
DEBSIGN_KEYID=0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
```

---

## 7. **Useful GPG Management Commands**

### View detailed key information:
```bash
gpg --list-secret-keys --keyid-format LONG
```

### Export key for backup:
```bash
gpg --export-secret-keys --armor 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5 > my-private-key.asc
```

### Import a key:
```bash
gpg --import my-private-key.asc
```

### Renew expiration:
```bash
gpg --edit-key 0AC196C690C4CH54FD5ARG465DSGSA4564A6SGD5
# Then type: expire
```

---

## 8. **Verify Everything Works**

```bash
echo "test" | gpg --clearsign
```

---

## 🚨 **Best Practices**

1. **Backup**: Store your private key in a secure location
2. **Expiration**: Use 1-2 years expiration for packaging keys
3. **Security**: Protect your key with a strong password
4. **Revocation**: Create a revocation certificate in case you lose the key

---

## 🔧 **Troubleshooting Common Issues**

### If gpg can't find the key:
```bash
export GPG_TTY=$(tty)
```

### If there are permission issues:
```bash
chmod 700 ~/.gnupg
```

### To verify package signature:
```bash
debsigs --verify my-package.deb
```

---

## 📝 **Additional Notes**

- Keep your private key secure and never share it
- Use the same email address as your Debian account
- Test your key setup before uploading packages
- Remember to renew your key before it expires

