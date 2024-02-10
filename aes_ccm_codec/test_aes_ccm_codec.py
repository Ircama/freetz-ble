import ctypes
so_file = "./aes_ccm_codec.so"
dll1 = ctypes.CDLL('libssl.so', mode=ctypes.RTLD_GLOBAL)
dll2 = ctypes.CDLL('libcrypto.so', mode=ctypes.RTLD_GLOBAL)

nonce = b'l2\xb38\xc1\xa4[\x05N/\x01\x00'
cipherpayload = b'\xd4F\xf0\xeb\x88'  # d4 46 f0 eb 88
mic = b'\xa6_\x8f+'  # a6 5f 8f 2b
update = b'\x11'
bindkey = b'_\xe6\x07\x14\x83\x88\x96\x07\xabK\xc7\xc3\x00\xe3C\xf3'

plain_text = b'\x04\x10\x02\xcf\x00'

my_library = ctypes.CDLL(so_file)
my_library.aes_ccm_decrypt.restype = ctypes.c_char_p
my_library.aes_ccm_encrypt.restype = ctypes.c_char_p

ret_msg = my_library.aes_ccm_encrypt(
    plain_text, len(plain_text),
    bindkey, len(bindkey),
    nonce, len(nonce),
    4,
    update, len(update),
    0
)
print("Cypher: ", ret_msg)


ret_msg = my_library.aes_ccm_decrypt(
    cipherpayload, len(cipherpayload),
    bindkey, len(bindkey),
    nonce, len(nonce),
    mic, len(mic),
    update, len(update),
    0
)
if ret_msg == b'error':
    print("Error!")
else:
    ret_bytes = bytes.fromhex(ret_msg.decode())
    if plain_text == ret_bytes:
        print("Decypher: ", ret_bytes.hex(' '))
    else:
        print("NO!")
