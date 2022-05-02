#!/usr/bin/python3

import re
import sys
import subprocess

# pylint: disable=invalid-name

### Sanity/usage checks

if len(sys.argv) != 3:
    print("E: need 2 arguments", file=sys.stderr)
    sys.exit(1)

version = sys.argv[1]
if version not in ["3", "4"]:
    print("E: unsupported version %s" % version, file=sys.stderr)
    sys.exit(1)

suite = sys.argv[2]
if suite not in ['ondokuz', 'yirmibir']:
    print("E: unsupported suite %s" % suite, file=sys.stderr)
    sys.exit(1)
target_yaml = 'raspi_%s_%s.yaml' % (version, suite)


### Setting variables based on suite and version starts here

# Arch, kernel, DTB:
if version in ['3', '4']:
    arch = 'arm64'
    linux = 'linux-image-arm64'
    dtb = '/usr/lib/linux-image-*-arm64/broadcom/bcm*rpi*.dtb'

# APT and default firmware (name + handling)
if suite == 'ondokuz':
    security_suite = '%s' % suite
    raspi_firmware = 'raspi3-firmware'
    fix_firmware = True
else:
    security_suite = '%s' % suite
    raspi_firmware = 'raspi-firmware'
    fix_firmware = False

# Extra wireless firmware:
wireless_firmware = ''

# Pi 4 on buster requires some backports:
backports_enable = False
backports_suite = '%s-backports' % suite
if version == '4' and suite == 'ondokuz':
    backports_enable = "# raspi 4 needs kernel and firmware newer than ondokuz's"
    linux = 'linux-image-arm64'
    raspi_firmware = 'raspi-firmware'
    wireless_firmware = 'firmware-brcm80211'
    fix_firmware = False

if version == '3' and suite == 'ondokuz':
    backports_enable = "# raspi 3 needs firmware-brcm80211 newer than ondokuz's for wifi"
    wireless_firmware = 'firmware-brcm80211'

# Serial console:
if version in ['3', '4']:
    serial = 'ttyS1,115200'

# CMA fixup:
extra_chroot_shell_cmds = []
if version == '4':
    extra_chroot_shell_cmds = [
        "sed -i 's/cma=64M //' /boot/firmware/cmdline.txt",
    ]

# XXX: The disparity between suite seems to be a bug, pick a naming
# and stick to it!
#
# Hostname:
if suite == 'ondokuz':
    hostname = 'rpi%s' % version
else:
    hostname = 'rpi_%s' % version

# Nothing yet!
extra_root_shell_cmds = []


### The following prepares substitutions based on variables set earlier

# Commands to fix the firmware name in the systemd unit:
if fix_firmware:
    fix_firmware_cmds = ['sed -i s/raspi-firmware/raspi3-firmware/ ${ROOT?}/etc/systemd/system/rpi-reconfigure-raspi-firmware.service']
else:
    fix_firmware_cmds = []

# Enable backports with a reason, or add commented-out entry:
if backports_enable:
    backports_stanza = """
%s
deb http://depo.pardus.org.tr/backports/ %s main contrib non-free
""" % (backports_enable, backports_suite)
else:
    backports_stanza = """
# Backports are _not_ enabled by default.
# Enable them by uncommenting the following line:
# deb http://depo.pardus.org.tr/backports/ %s main contrib non-free
""" % backports_suite

# Buster requires an existing, empty /etc/machine-id file:
if suite == 'ondokuz':
    touch_machine_id = 'touch /etc/machine-id'
else:
    touch_machine_id = ''

# Buster shipped timesyncd directly into systemd:
if suite == 'ondokuz':
    systemd_timesyncd = 'systemd'
else:
    systemd_timesyncd = 'systemd-timesyncd'

gitcommit = subprocess.getoutput("git show -s --pretty='format:%C(auto)%h (%s, %ad)' --date=short ")
buildtime = subprocess.getoutput("date --utc +'%Y-%m-%d %H:%M'")

### Write results:

def align_replace(text, pattern, replacement):
    """
    This helper lets us keep the indentation of the matched pattern
    with the upcoming replacement, across multiple lines. Naive
    implementation, please make it more pythonic!
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'^(\s+)%s' % pattern, line)
        if m:
            indent = m.group(1)
            del lines[i]
            for r in replacement:
                lines.insert(i, '%s%s' % (indent, r))
                i = i + 1
            break
    return '\n'. join(lines) + '\n'


with open('raspi_master.yaml', 'r') as in_file:
    with open(target_yaml, 'w') as out_file:
        in_text = in_file.read()
        out_text = in_text \
            .replace('__RELEASE__', suite) \
            .replace('__ARCH__', arch) \
            .replace('__LINUX_IMAGE__', linux) \
            .replace('__DTB__', dtb) \
            .replace('__SECURITY_SUITE__', security_suite) \
            .replace('__SYSTEMD_TIMESYNCD__', systemd_timesyncd) \
            .replace('__RASPI_FIRMWARE__', raspi_firmware) \
            .replace('__WIRELESS_FIRMWARE__', wireless_firmware) \
            .replace('__SERIAL_CONSOLE__', serial) \
            .replace('__HOST__', hostname) \
            .replace('__TOUCH_MACHINE_ID__', touch_machine_id) \
            .replace('__GITCOMMIT__', gitcommit) \
            .replace('__BUILDTIME__', buildtime)

        out_text = align_replace(out_text, '__FIX_FIRMWARE_PKG_NAME__', fix_firmware_cmds)
        out_text = align_replace(out_text, '__EXTRA_ROOT_SHELL_CMDS__', extra_root_shell_cmds)
        out_text = align_replace(out_text, '__EXTRA_CHROOT_SHELL_CMDS__', extra_chroot_shell_cmds)
        out_text = align_replace(out_text, '__BACKPORTS__', backports_stanza.splitlines())

        # Try not to keep lines where the placeholder was replaced
        # with nothing at all (including on a "list item" line):
        filtered = [x for x in out_text.splitlines()
                    if not re.match(r'^\s+$', x)
                    and not re.match(r'^\s+-\s*$', x)]
        out_file.write('\n'.join(filtered) + "\n")
