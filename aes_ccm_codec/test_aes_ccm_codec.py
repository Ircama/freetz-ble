from __future__ import print_function
import ctypes
import os
import binascii

# Load the libraries
so_file = "./aes_ccm_codec.so"
dll1 = ctypes.CDLL('libssl.so', mode=ctypes.RTLD_GLOBAL)
dll2 = ctypes.CDLL('libcrypto.so', mode=ctypes.RTLD_GLOBAL)
my_library = ctypes.CDLL(so_file)

# Set return types for all functions
my_library.aes_ccm_decrypt.restype = ctypes.c_char_p
my_library.aes_ccm_encrypt.restype = ctypes.c_char_p
my_library.aes_gcm_decrypt.restype = ctypes.c_char_p
my_library.aes_gcm_encrypt.restype = ctypes.c_char_p

# Test data for CCM
ccm_nonce = b'l2\xb38\xc1\xa4[\x05N/\x01\x00'
ccm_cipherpayload = b'\xd4F\xf0\xeb\x88'  # d4 46 f0 eb 88
ccm_mic = b'\xa6_\x8f+'  # a6 5f 8f 2b
ccm_update = b'\x11'
ccm_bindkey = b'_\xe6\x07\x14\x83\x88\x96\x07\xabK\xc7\xc3\x00\xe3C\xf3'
ccm_plain_text = b'\x04\x10\x02\xcf\x00'

# Test data for GCM
# Using same key as CCM for comparison
gcm_key = ccm_bindkey  
# GCM typically uses 12-byte IV (96 bits)
gcm_iv = b'GCMiv123456' 
gcm_plain_text = b'\x04\x10\x02\xcf\x00'  # Same as CCM
gcm_aad = b'\x11'  # Same as CCM update

print("=" * 50)
print("TESTING AES CCM MODE")
print("=" * 50)

# Test CCM encryption
print("\nCCM Encryption Test:")
ret_msg = my_library.aes_ccm_encrypt(
    ccm_plain_text, len(ccm_plain_text),
    ccm_bindkey, len(ccm_bindkey),
    ccm_nonce, len(ccm_nonce),
    4,  # tag length
    ccm_update, len(ccm_update),
    0   # debug mode off
)
print("CCM Encryption Result:", ret_msg.decode())

# Parse the encryption result
ccm_parts = ret_msg.decode().split()
if len(ccm_parts) >= 2:
    ccm_encrypted_hex = ccm_parts[0]
    ccm_tag_hex = ccm_parts[1]
    print("CCM Ciphertext (hex):", ccm_encrypted_hex)
    print("CCM Tag (hex):", ccm_tag_hex)
    
    # Convert hex to bytes for comparison
    ccm_encrypted_bytes = binascii.unhexlify(ccm_encrypted_hex)
    ccm_tag_bytes = binascii.unhexlify(ccm_tag_hex)
    
    # Compare with expected values
    print("\nVerifying against expected values:")
    print("Expected ciphertext:", binascii.hexlify(ccm_cipherpayload).decode())
    print("Actual ciphertext:", ccm_encrypted_hex)
    print("Match:", ccm_encrypted_bytes == ccm_cipherpayload)
    
    print("Expected tag:", binascii.hexlify(ccm_mic).decode())
    print("Actual tag:", ccm_tag_hex)
    print("Match:", ccm_tag_bytes == ccm_mic)

# Test CCM decryption
print("\nCCM Decryption Test:")
ret_msg = my_library.aes_ccm_decrypt(
    ccm_cipherpayload, len(ccm_cipherpayload),
    ccm_bindkey, len(ccm_bindkey),
    ccm_nonce, len(ccm_nonce),
    ccm_mic, len(ccm_mic),
    ccm_update, len(ccm_update),
    0  # debug mode off
)

if ret_msg == b'error':
    print("CCM Decryption Error!")
else:
    ret_bytes = binascii.unhexlify(ret_msg.decode())
    if ccm_plain_text == ret_bytes:
        print("CCM Decryption Success!")
        print("Decrypted plaintext (hex):", binascii.hexlify(ret_bytes))
    else:
        print("CCM Decryption Failed - Incorrect plaintext!")
        print("Expected:", binascii.hexlify(ccm_plain_text).decode())
        print("Actual:",  binascii.hexlify(ret_bytes))

print("\n" + "=" * 50)
print("TESTING AES GCM MODE")
print("=" * 50)

# Step 1: Encrypt data with GCM
print("\nGCM Encryption Test:")
ret_msg = my_library.aes_gcm_encrypt(
    gcm_plain_text, len(gcm_plain_text),
    gcm_key, len(gcm_key),
    gcm_iv, len(gcm_iv),
    16,  # 16-byte (128-bit) tag
    gcm_aad, len(gcm_aad),
    0    # debug mode off
)
print("GCM Encryption Result:", ret_msg.decode())

# Parse the encryption result
gcm_parts = ret_msg.decode().split()
if len(gcm_parts) >= 2:
    gcm_encrypted_hex = gcm_parts[0]
    gcm_tag_hex = gcm_parts[1]
    print("GCM Ciphertext (hex):", gcm_encrypted_hex)
    print("GCM Tag (hex):", gcm_tag_hex)
    
    # Convert hex to bytes for decryption test
    gcm_encrypted_bytes = binascii.unhexlify(gcm_encrypted_hex)
    gcm_tag_bytes = binascii.unhexlify(gcm_tag_hex)

# Step 2: Decrypt the data with GCM
print("\nGCM Decryption Test:")
ret_msg = my_library.aes_gcm_decrypt(
    gcm_encrypted_bytes, len(gcm_encrypted_bytes),
    gcm_key, len(gcm_key),
    gcm_iv, len(gcm_iv),
    gcm_tag_bytes, len(gcm_tag_bytes),
    gcm_aad, len(gcm_aad),
    0    # debug mode off
)

if ret_msg == b'error':
    print("GCM Decryption Error!")
else:
    ret_bytes = binascii.unhexlify(ret_msg.decode())
    if gcm_plain_text == ret_bytes:
        print("GCM Decryption Success!")
        print("Decrypted plaintext (hex):", binascii.hexlify(ret_bytes))
    else:
        print("GCM Decryption Failed - Incorrect plaintext!")
        print("Expected:", binascii.hexlify(gcm_plain_text).decode())
        print("Actual:", binascii.hexlify(ret_bytes))

# Step 3: Test GCM tag verification by corrupting the tag
print("\nGCM Tag Verification Test (with corrupted tag):")
# Create a corrupted tag by flipping a bit
corrupted_tag = bytearray(gcm_tag_bytes)
corrupted_tag[0] ^= 1  # Flip the first bit
# Convert back to bytes before passing to C function
corrupted_tag_bytes = bytes(corrupted_tag)
ret_msg = my_library.aes_gcm_decrypt(
    gcm_encrypted_bytes, len(gcm_encrypted_bytes),
    gcm_key, len(gcm_key),
    gcm_iv, len(gcm_iv),
    corrupted_tag_bytes, len(corrupted_tag_bytes),
    gcm_aad, len(gcm_aad),
    0    # debug mode off
)

if ret_msg == b'error':
    print("GCM Tag Verification Test Passed: Decryption correctly failed with corrupted tag")
else:
    print("GCM Tag Verification Test Failed: Decryption succeeded with corrupted tag!")

# Step 4: Test GCM with different IV
print("\nGCM Different IV Test:")
different_iv = b'DiffIV123456'
ret_msg = my_library.aes_gcm_encrypt(
    gcm_plain_text, len(gcm_plain_text),
    gcm_key, len(gcm_key),
    different_iv, len(different_iv),
    16,  # 16-byte tag
    gcm_aad, len(gcm_aad),
    0    # debug mode off
)
print("GCM Encryption with Different IV Result:", ret_msg.decode())

different_iv_parts = ret_msg.decode().split()
if len(different_iv_parts) >= 2:
    different_iv_encrypted_hex = different_iv_parts[0]
    different_iv_tag_hex = different_iv_parts[1]
    
    # Compare with original encryption
    print("Different IV produces different ciphertext:", different_iv_encrypted_hex != gcm_encrypted_hex)
    print("Different IV produces different tag:", different_iv_tag_hex != gcm_tag_hex)

# Step 5: Test GCM with debug mode
print("\nGCM Debug Mode Test:")
ret_msg = my_library.aes_gcm_encrypt(
    gcm_plain_text, len(gcm_plain_text),
    gcm_key, len(gcm_key),
    gcm_iv, len(gcm_iv),
    16,  # 16-byte tag
    gcm_aad, len(gcm_aad),
    1    # debug mode on
)
print("Debug output produced. Check console for details.")
