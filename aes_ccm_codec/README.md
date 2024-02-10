# aes_ccm_codec

This project reuses the *aesccm.c* code included in freetz (OpenSSL crypto libraries) at source/target-mips_gcc-13.2.0_uClibc-1.0.45-nptl_kernel-4.9/openssl-3.0.13/demos/cipher/aesccm.c, which is a simple demonstration program to test the AES CCM authenticated encryption with additional data (AEAD).

The code is changed in order to:

- export the two `aes_ccm_decrypt` and `aes_ccm_encrypt` C functions,
- support the AES CCM mode used by BLE home sensors (AES-128-CCM and not AES-192-CCM),
- map the naming convention of the encryption parameters used by the BLE home sensors,
- allow Python2.7 integration (this is in place of the AES CCM mode provided by the [pycryptodome](https://pypi.org/project/pycryptodome/) library, that *freetz* does not include).

A simple example of Python 2.7 integration is also included (*test_aes_ccm_codec.py*).

- Compiling the code with cross-compiler for FRITZ!Box:

```
/home/$USER/freetz-ng/toolchain/build/mips_gcc-13.2.0_uClibc-1.0.45-nptl_kernel-4.9/mips-linux-uclibc/bin/mips-linux-uclibc-gcc -march=34kc -mtune=34kc -msoft-float -Ofast -pipe -Wa,--trap -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -Wl,-I/usr/lib/freetz/ld-uClibc.so.1 -shared -o aes_ccm_codec.so -fPIC aes_ccm_codec.c -lssl -lcrypto
```

- Compiling le code with Ubuntu:

```
gcc -lssl -lcrypto -o aes_ccm_codec -shared -o aes_ccm_codec.so -fPIC aes_ccm_codec.c
```

The included `aes_ccm_codec.so` library can be directly used in a FRITZ!Box.
