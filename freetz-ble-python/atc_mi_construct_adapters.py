#coding=utf-8
# Library module used by atc_mi_construct.py

from construct import *  # pip3 install construct
import re
import ctypes
import codecs
from itertools import chain

MacVendor = Switch(
    this.MAC[:9],
    {
        "A4:C1:38:": Computed("Telink Semiconductor (Taipei) Co. Ltd"),
        "54:EF:44:": Computed("Lumi United Technology Co., Ltd"),
        "E4:AA:EC:": Computed("Tianjin Hualai Tech Co, Ltd"),
    },
    default=Computed("Unknown vendor"),
)


def dict_union(*args):
    return dict(chain.from_iterable(d.iteritems() for d in args))

so_file = "/var/mod/root/aes_ccm_codec.so"
dll1 = ctypes.CDLL('libssl.so', mode=ctypes.RTLD_GLOBAL)
dll2 = ctypes.CDLL('libcrypto.so', mode=ctypes.RTLD_GLOBAL)

codec_library = ctypes.CDLL(so_file)
codec_library.aes_ccm_decrypt.restype = ctypes.c_char_p
codec_library.aes_ccm_encrypt.restype = ctypes.c_char_p


def handle_decrypt_error(descr):  # can be monkey patched
    raise ValueError(descr)


class BtHomeCodec(Tunnel):
    def __init__(self, subcon, bindkey=b'', mac_address=b''):
        super(Tunnel, self).__init__(subcon)
        self.default_bindkey = bindkey
        self.def_mac = mac_address

    def bindkey(self, ctx):
        try:
            return ctx._params.bindkey or self.default_bindkey
        except Exception:
            return self.default_bindkey

    def mac(self, ctx, msg="encode or decode"):
        try:
            mac = ctx._params.mac_address or self.def_mac
        except Exception:
            mac = self.def_mac
        if not mac.strip():
            return handle_decrypt_error('Missing MAC address. Cannot convert.')
        return mac.strip()

    def _decode(self, obj, ctx, path):
        mac = self.mac(ctx, "decode")
        pkt = ctx._io.getvalue()[2:]
        uuid = pkt[0:2]
        cipherpayload = pkt[2:-8]
        count_id = pkt[-8:-4]  # Int32ul
        mic = pkt[-4:]
        nonce = mac + uuid + count_id
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot decrypt.')
        try:
            ret_msg = codec_library.aes_ccm_decrypt(
                cipherpayload, len(cipherpayload),
                bindkey, len(bindkey),
                nonce, len(nonce),
                mic, len(mic),
                b"\x11", 1,
                0
            )
        except Exception as e:
            return handle_decrypt_error("Cannot decrypt: " + str(e))
        if ret_msg == b'error':
            return handle_decrypt_error("Invalid decrypt parameters.")
        return count_id + codecs.decode(ret_msg.decode(), "hex")

    def _encode(self, obj, ctx, path):
        mac = self.mac(ctx, "encode")
        length_count_id = 4  # first 4 bytes = 32 bits
        count_id = bytes(obj)[:length_count_id]  # Int32ul
        uuid16 = b"\x1e\x18"
        nonce = mac + uuid16 + count_id
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot encrypt.')
        ret_msg = codec_library.aes_ccm_encrypt(
            obj[length_count_id:], len(obj[length_count_id:]),
            bindkey, len(bindkey),
            nonce, len(nonce),
            4,
            b"\x11", 1,
            0
        )
        ciphertext = codecs.decode(ret_msg.split()[0], "hex")
        mic = codecs.decode(ret_msg.split()[1], "hex")
        return ciphertext + count_id + mic


class BtHomeV2Codec(BtHomeCodec):
    def _decode(self, obj, ctx, path):
        mac = self.mac(ctx, "decode")
        pkt = ctx._io.getvalue()[2:]
        uuid = pkt[0:2]
        device_info = pkt[2:3]
        encrypted_data = pkt[3:-8]
        count_id = pkt[-8:-4]  # Int32ul
        mic = pkt[-4:]
        nonce = mac + uuid + device_info + count_id
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot decrypt.')
        try:
            ret_msg = codec_library.aes_ccm_decrypt(
                encrypted_data, len(encrypted_data),
                bindkey, len(bindkey),
                nonce, len(nonce),
                mic, len(mic),
                b"", 0,
                0
            )
        except Exception as e:
            return handle_decrypt_error("Cannot decrypt: " + str(e))
        if ret_msg == b'error':
            return handle_decrypt_error("Invalid decrypt parameters.")
        return count_id + codecs.decode(ret_msg.decode(), "hex")

    def _encode(self, obj, ctx, path):
        mac = self.mac(ctx, "encode")
        length_count_id = 4  # first 4 bytes = 32 bits
        count_id = bytes(obj)[:length_count_id]  # Int32ul
        uuid16 = b"\xd2\xfc"
        device_info = b"\x41"
        nonce = mac + uuid16 + device_info + count_id
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot encrypt.')
        ret_msg = codec_library.aes_ccm_encrypt(
            bytes(obj)[length_count_id:], len(bytes(obj)[length_count_id:]),
            bindkey, len(bindkey),
            nonce, len(nonce),
            4,
            b"", 0,
            0
        )
        ciphertext = codecs.decode(ret_msg.split()[0], "hex")
        mic = codecs.decode(ret_msg.split()[1], "hex")
        return ciphertext + count_id + mic


class AtcMiCodec(BtHomeCodec):
    def _decode(self, obj, ctx, path):
        mac = self.mac(ctx, "decode")
        payload = bytes(obj)[1:]
        cipherpayload = payload[:-4]
        header_bytes = ctx._io.getvalue()[:4]  # b'\x0e\x16\x1a\x18' (custom_enc) or b'\x0b\x16\x1a\x18' (atc1441_enc)
        nonce = mac[::-1] + header_bytes + bytes(obj)[:1]
        mic = payload[-4:]
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot decrypt.')
        try:
            ret_msg = codec_library.aes_ccm_decrypt(
                cipherpayload, len(cipherpayload),
                bindkey, len(bindkey),
                nonce, len(nonce),
                mic, len(mic),
                b"\x11", 1,
                0
            )
        except Exception as e:
            return handle_decrypt_error("Cannot decrypt: " + str(e))
        if ret_msg == b'error':
            return handle_decrypt_error("Invalid decrypt parameters.")
        return codecs.decode(ret_msg.decode(), "hex")

    def _encode(self, obj, ctx, path):
        mac = self.mac(ctx, "encode")
        header_bytes = ctx._io.getvalue()[:4] + b'\xbd'  # b'\x0e\x16\x1a\x18\xbd' (custom_enc) or b'\x0b\x16\x1a\x18\xbd' (atc1441_enc)
        nonce = mac[::-1] + header_bytes
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot encrypt.')
        ret_msg = codec_library.aes_ccm_encrypt(
            obj, len(obj),
            bindkey, len(bindkey),
            nonce, len(nonce),
            4,
            b"\x11", 1,
            0
        )
        ciphertext = codecs.decode(ret_msg.split()[0], "hex")
        mic = codecs.decode(ret_msg.split()[1], "hex")
        return b'\xbd' + ciphertext + mic


class MiLikeCodec(BtHomeCodec):
    def _decode(self, obj, ctx, path):
        payload = obj
        cipherpayload = payload[:-7]
        mac = self.mac(ctx, "decode")
        dev_id = ctx._io.getvalue()[6:8]  # pid, PRODUCT_ID
        cnt = ctx._io.getvalue()[8:9]  # encode frame cnt
        count_id = payload[-7:-4]  # Int24ul
        nonce = mac[::-1] + dev_id + cnt + count_id
        mic = payload[-4:]
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot decrypt.')
        try:
            ret_msg = codec_library.aes_ccm_decrypt(
                cipherpayload, len(cipherpayload),
                bindkey, len(bindkey),
                nonce, len(nonce),
                mic, len(mic),
                b"\x11", 1,
                0
            )
        except Exception as e:
            return handle_decrypt_error("Cannot decrypt: " + str(e))
        if ret_msg == b'error':
            return handle_decrypt_error("Invalid decrypt parameters.")
        return count_id + codecs.decode(ret_msg.decode(), "hex")

    def _encode(self, obj, ctx, path):
        mac = self.mac(ctx, "encode")
        dev_id = ctx._io.getvalue()[6:8]  # pid, PRODUCT_ID
        cnt = ctx._io.getvalue()[8:9]  # encode frame cnt
        length_count_id = 3  # first 3 bytes = 24 bits
        count_id = bytes(obj)[:length_count_id]  # Int24ul
        nonce = mac[::-1] + dev_id + cnt + count_id
        bindkey = self.bindkey(ctx)
        if not bindkey:
            return handle_decrypt_error('Missing bindkey, cannot encrypt.')
        ret_msg = codec_library.aes_ccm_encrypt(
            obj[length_count_id:], len(obj[length_count_id:]),
            bindkey, len(bindkey),
            nonce, len(nonce),
            4,
            b"\x11", 1,
            0
        )
        ciphertext = codecs.decode(ret_msg.split()[0], "hex")
        mic = codecs.decode(ret_msg.split()[1], "hex")
        return ciphertext + count_id + mic


class DecimalNumber(Adapter):
    def __init__(self, subcon, decimal):
        self.decimal = decimal
        super(Adapter, self).__init__(subcon)
        self._decode = lambda obj, ctx, path: float(obj) / self.decimal
        self._encode = lambda obj, ctx, path: int(float(obj) * self.decimal)


MacAddress = ExprAdapter(Byte[6],
    decoder = lambda obj, ctx: ":".join("%02x" % b for b in obj).upper(),
    encoder = lambda obj, ctx: bytes.fromhex(re.sub(r'[.:\- ]', '', obj))
)
ReversedMacAddress = ExprAdapter(Byte[6],
    decoder = lambda obj, ctx: ":".join("%02x" % b for b in obj[::-1]).upper(),
    encoder = lambda obj, ctx: bytes.fromhex(re.sub(r'[.:\- ]', '', obj))[::-1]
)
