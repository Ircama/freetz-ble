# Superseded Note

This library is **superseded by** the [`python-pycryptodome`](https://github.com/Freetz-NG/freetz-ng/commit/3fdb9e4c185f908e07cb249d5c918f986b035454) package.

# aes_ccm_gcm_codec

This project extends and enhances the *aesccm.c* code included in freetz (OpenSSL crypto libraries) at source/target-mips_gcc-13.2.0_uClibc-1.0.45-nptl_kernel-4.9/openssl-3.0.13/demos/cipher/aesccm.c, which is a simple demonstration program for authenticated encryption with additional data (AEAD).

## Features

The code has been enhanced to:

- Export four C functions: `aes_ccm_decrypt`, `aes_ccm_encrypt`, `aes_gcm_decrypt`, and `aes_gcm_encrypt`
- Support AES CCM mode used by BLE home sensors (AES-128-CCM)
- Support AES GCM mode for enhanced performance and flexibility
- Map the naming convention of encryption parameters used by BLE home sensors
- Allow Python2.7/Python3 integration (as a replacement for the AES modes provided by the [pycryptodome](https://pypi.org/project/pycryptodome/) library, which *freetz* does not include)

## Supported Encryption Modes

### AES CCM (Counter with CBC-MAC)
- Good for resource-constrained environments
- Requires knowledge of plaintext length before encryption
- Compatible with BLE home sensors

### AES GCM (Galois/Counter Mode)
- Better performance on systems with hardware support
- Does not require knowledge of plaintext length before encryption
- Widely used in TLS and other secure protocols

## Compilation

### For FRITZ!Box (Cross-compilation)

```bash
/home/$USER/freetz-ng/toolchain/build/mips_gcc-13.2.0_uClibc-1.0.45-nptl_kernel-4.9/mips-linux-uclibc/bin/mips-linux-uclibc-gcc -march=34kc -mtune=34kc -msoft-float -Ofast -pipe -Wa,--trap -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -Wl,-I/usr/lib/freetz/ld-uClibc.so.1 -shared -o aes_ccm_gcm_codec.so -fPIC aes_ccm_gcm_codec.c -lssl -lcrypto
```

or

```bash
/home/$USER/freetz-ng/toolchain/build/mips_gcc-13.3.0_uClibc-1.0.52-nptl_kernel-4.9/mips-linux-uclibc/bin/mips-linux-uclibc-gcc -march=34kc -mtune=34kc -msoft-float -Ofast -pipe -Wa,--trap -D_LARGEFILE_SOURCE -D_LARGEFILE64_SOURCE -D_FILE_OFFSET_BITS=64 -Wl,-I/usr/lib/freetz/ld-uClibc.so.1 -shared -o aes_ccm_codec.so -fPIC aes_ccm_codec.c -lssl -lcrypto
```

### For Ubuntu/Linux

```bash
gcc -lssl -lcrypto -shared -o aes_ccm_gcm_codec.so -fPIC aes_ccm_gcm_codec.c
```

## Usage Examples

### Python Integration

The repository includes example Python scripts (`test_aes_ccm_codec.py` and `test_aes_gcm_codec.py`) demonstrating how to use both encryption modes from Python.

Basic CCM example:
```python
import ctypes
so_file = "./aes_ccm_gcm_codec.so"
my_library = ctypes.CDLL(so_file)
my_library.aes_ccm_decrypt.restype = ctypes.c_char_p
# Call the CCM function with appropriate parameters
```

Basic GCM example:
```python
import ctypes
so_file = "./aes_ccm_gcm_codec.so"
my_library = ctypes.CDLL(so_file)
my_library.aes_gcm_encrypt.restype = ctypes.c_char_p
# Call the GCM function with appropriate parameters
```

## Library Files

The included `aes_ccm_gcm_codec.so` library can be directly used in a FRITZ!Box or similar environments.

## Dependencies

- OpenSSL 3.0+ (for the crypto libraries)
- A C compiler (gcc recommended)

## License

This code is subject to the same licensing as the original OpenSSL demos.

## Output of test_aes_ccm_codec.py

```
==================================================
TESTING AES CCM MODE
==================================================

CCM Encryption Test:
CCM Encryption Result: D446F0EB88 A65F8F2B
CCM Ciphertext (hex): D446F0EB88
CCM Tag (hex): A65F8F2B

Verifying against expected values:
Expected ciphertext: d446f0eb88
Actual ciphertext: D446F0EB88
Match: True
Expected tag: a65f8f2b
Actual tag: A65F8F2B
Match: True

CCM Decryption Test:
CCM Decryption Success!
Decrypted plaintext (hex): b'041002cf00'

==================================================
TESTING AES GCM MODE
==================================================

GCM Encryption Test:
GCM Encryption Result: FE63EB00AD 63D3ADB83F75447D1D1BAA12652D6423
GCM Ciphertext (hex): FE63EB00AD
GCM Tag (hex): 63D3ADB83F75447D1D1BAA12652D6423

GCM Decryption Test:
GCM Decryption Success!
Decrypted plaintext (hex): b'041002cf00'

GCM Tag Verification Test (with corrupted tag):
GCM Tag Verification Test Passed: Decryption correctly failed with corrupted tag

GCM Different IV Test:
GCM Encryption with Different IV Result: 715549D32A E033459AF85CDCDBBFEA259DDCDBCF63
Different IV produces different ciphertext: True
Different IV produces different tag: True

GCM Debug Mode Test:
AES GCM Encrypt:
Plaintext:
0000 - 04 10 02 cf 00                                    .....
AAD:
0000 - 11                                                .
Ciphertext:
0000 - fe 63 eb 00 ad                                    .c...
Tag:
0000 - 63 d3 ad b8 3f 75 44 7d-1d 1b aa 12 65 2d 64 23   c...?uD}....e-d#
Debug output produced. Check console for details.
```
