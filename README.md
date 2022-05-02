# Raspberry Pi Pardus

Bu araç ile kendi Pardus imaj dosyalarınızı oluşturabilirsiniz.

Depoyu klonlayın.

```shell
git clone --recursive https://github.com/dkey5/image-specs.git
cd image-specs
```

Derlemek için gereken paketler:
* binfmt-support
* bmap-tools
* debootstrap
* dosfstools
* fakemachine
* kpartx
* qemu-utils
* qemu-user-static
* time
* vmdb2 (>= 0.17)
* python3

```shell
   apt install -y vmdb2 dosfstools qemu-utils qemu-user-static debootstrap binfmt-support time kpartx bmap-tools python3
   apt install -y fakemachine
```

## Raspberry Pi 3 Pardus(ondokuz)
```shell
   make raspi_3_ondokuz.img
```

## Raspberry Pi 3 Pardus(yirmibir):
```shell
   make raspi_3_yirmibir.img
```

## Raspberry Pi 4 Pardus(ondokuz):
raspi-firmware paketi Pardus(ondokuz) depolarında olmamasından dolayı derlenememiştir.

## Raspberry Pi 4 Pardus(yirmibir):
```shell
   make raspi_4_yirmibir.img
```
