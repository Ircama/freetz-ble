#include <stdio.h>
#include <openssl/err.h>
#include <openssl/bio.h>
#include <openssl/evp.h>
#include <openssl/core_names.h>

/*
 * A library context and property query can be used to select & filter
 * algorithm implementations. If they are NULL then the default library
 * context and properties are used.
 */
OSSL_LIB_CTX *libctx = NULL;
const char *propq = NULL;
static unsigned char text_buf[1024];

char * aes_ccm_decrypt(
    unsigned char * ccm_ct, int ccm_ct_len,  // encrypted_data
    unsigned char * ccm_key, int ccm_key_len,  // bindkey
    unsigned char * ccm_nonce, size_t ccm_nonce_len,  // nonce
    unsigned char * ccm_tag, int ccm_tag_len,  // mic; mac_len is its length
    unsigned char * ccm_adata, int ccm_adata_len,  // update
    int debug  // 0 (no debug) or 1 (debug)
) {
    int i = 0;
    EVP_CIPHER_CTX *ctx;
    EVP_CIPHER *cipher = NULL;
    int outlen, rv;
    unsigned char outbuf[1024];
    unsigned char *ptr;

    if (debug) {
        printf("AES CCM Decrypt:\n\n");
    }

    if (debug) {
        printf("nonce:\n");
        BIO_dump_fp(stdout, ccm_nonce, ccm_nonce_len);
        printf("\nnonce length: %ld\n", ccm_nonce_len);
    }

    OSSL_PARAM params[3] = {
        OSSL_PARAM_END, OSSL_PARAM_END, OSSL_PARAM_END
    };

    if (debug) {
        printf("\nccm_ct Ciphertext:\n");
        BIO_dump_fp(stdout, ccm_ct, ccm_ct_len);
    }

    if ((ctx = EVP_CIPHER_CTX_new()) == NULL)
        goto err;

    /* Fetch the cipher implementation */
    if ((cipher = EVP_CIPHER_fetch(libctx, "AES-128-CCM", propq)) == NULL)
        goto err;

    /* Set nonce length if default 96 bits is not appropriate */
    params[0] = OSSL_PARAM_construct_size_t(OSSL_CIPHER_PARAM_AEAD_IVLEN,
                                            &ccm_nonce_len);

    if (debug) {
        printf("\nccm_tag mic:\n");
        BIO_dump_fp(stdout, ccm_tag, ccm_tag_len);
    }

    /* Set tag length */
    params[1] = OSSL_PARAM_construct_octet_string(OSSL_CIPHER_PARAM_AEAD_TAG,
                                                  (unsigned char *)ccm_tag,
                                                  ccm_tag_len);

    /*
     * Initialise decrypt operation with the cipher & mode,
     * nonce length and expected tag parameters.
     */
    if (!EVP_DecryptInit_ex2(ctx, cipher, NULL, NULL, params))
        goto err;

    if (debug) {
        printf("\nccm_key bindkey:\n");
        BIO_dump_fp(stdout, ccm_key, ccm_key_len);
    }

    /* Specify key and IV */
    if (!EVP_DecryptInit_ex(ctx, NULL, NULL, ccm_key, ccm_nonce))
        goto err;

    /* Set ciphertext length: only needed if we have AAD */
    if (!EVP_DecryptUpdate(ctx, NULL, &outlen, NULL, ccm_ct_len))
        goto err;

    /* Zero or one call to specify any AAD */
    if (!EVP_DecryptUpdate(ctx, NULL, &outlen, ccm_adata, ccm_adata_len))
        goto err;

    if (debug) {
        printf("\nccm_adata update:\n");
        BIO_dump_fp(stdout, ccm_adata, ccm_adata_len);
    }

    /* Decrypt plaintext, verify tag: can only be called once */
    rv = EVP_DecryptUpdate(ctx, outbuf, &outlen, ccm_ct, ccm_ct_len);

    /* Output decrypted block: if tag verify failed we get nothing */
    if (rv > 0) {
        if (debug) {
            printf("Tag verify successful!\nPlaintext:\n");
            BIO_dump_fp(stdout, outbuf, outlen);
        }
        
        ptr = text_buf;
        for (i = 0; i < outlen; i++) {
            ptr += sprintf(ptr, "%02X", outbuf[i]);
        }
        EVP_CIPHER_free(cipher);
        EVP_CIPHER_CTX_free(ctx);
        return text_buf;
    } else {
        if (debug) {
            printf("Tag verify failed!\nPlaintext not available\n");
        }
        goto err;
    }
err:
    if (debug) {
        ERR_print_errors_fp(stderr);
    }

    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);

    return "error";
}

char * aes_ccm_encrypt(
    unsigned char * ccm_pt, int ccm_pt_len,  // encrypted_data
    unsigned char * ccm_key, int ccm_key_len,  // bindkey
    unsigned char * ccm_nonce, size_t ccm_nonce_len,  // nonce
    int ccm_tag_len,  // mac_len
    unsigned char * ccm_adata, int ccm_adata_len,  // update
    int debug  // 0 (no debug) or 1 (debug)
) {
    int i = 0;
    EVP_CIPHER_CTX *ctx;
    EVP_CIPHER *cipher = NULL;
    int outlen, tmplen;
    unsigned char outbuf[1024];
    unsigned char outtag[16];
    OSSL_PARAM params[3] = {
        OSSL_PARAM_END, OSSL_PARAM_END, OSSL_PARAM_END
    };
    unsigned char *ptr = text_buf;

    if (debug) {    
        printf("AES CCM Encrypt:\n");
        printf("Plaintext:\n");
        BIO_dump_fp(stdout, ccm_pt, ccm_pt_len);
    }

    /* Create a context for the encrypt operation */
    if ((ctx = EVP_CIPHER_CTX_new()) == NULL)
        goto err;

    /* Fetch the cipher implementation */
    if ((cipher = EVP_CIPHER_fetch(libctx, "AES-128-CCM", propq)) == NULL)
        goto err;

    /* Set nonce length if default 96 bits is not appropriate */
    params[0] = OSSL_PARAM_construct_size_t(OSSL_CIPHER_PARAM_AEAD_IVLEN,
                                            &ccm_nonce_len);
    /* Set tag length */
    params[1] = OSSL_PARAM_construct_octet_string(OSSL_CIPHER_PARAM_AEAD_TAG,
                                                  NULL, ccm_tag_len);

    /*
     * Initialise encrypt operation with the cipher & mode,
     * nonce length and tag length parameters.
     */
    if (!EVP_EncryptInit_ex2(ctx, cipher, NULL, NULL, params))
        goto err;

    /* Initialise key and nonce */
    if (!EVP_EncryptInit_ex(ctx, NULL, NULL, ccm_key, ccm_nonce))
        goto err;

    /* Set plaintext length: only needed if AAD is used */
    if (!EVP_EncryptUpdate(ctx, NULL, &outlen, NULL, ccm_pt_len))
        goto err;

    /* Zero or one call to specify any AAD */
    if (!EVP_EncryptUpdate(ctx, NULL, &outlen, ccm_adata, ccm_adata_len))
        goto err;

    /* Encrypt plaintext: can only be called once */
    if (!EVP_EncryptUpdate(ctx, outbuf, &outlen, ccm_pt, ccm_pt_len))
        goto err;

    /* Output encrypted block */
    if (debug) {    
        printf("Ciphertext:\n");
        BIO_dump_fp(stdout, outbuf, outlen);
    }

    for (i = 0; i < outlen; i++) {
        ptr += sprintf(ptr, "%02X", outbuf[i]);
    }
    ptr += sprintf(ptr, " ");

    /* Finalise: note get no output for CCM */
    if (!EVP_EncryptFinal_ex(ctx, NULL, &tmplen))
        goto err;

    /* Get tag */
    params[0] = OSSL_PARAM_construct_octet_string(OSSL_CIPHER_PARAM_AEAD_TAG,
                                                  outtag, ccm_tag_len);
    params[1] = OSSL_PARAM_construct_end();

    if (!EVP_CIPHER_CTX_get_params(ctx, params))
        goto err;

    /* Output tag */
    if (debug) {    
        printf("Tag:\n");
        BIO_dump_fp(stdout, outtag, ccm_tag_len);
    }

    for (i = 0; i < ccm_tag_len; i++) {
        ptr += sprintf(ptr, "%02X", outtag[i]);
    }
    return text_buf;
    
err:
    ERR_print_errors_fp(stderr);

    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);

    return "error";
}

/* AES GCM Decrypt function */
char * aes_gcm_decrypt(
    unsigned char * gcm_ct, int gcm_ct_len,  // encrypted_data
    unsigned char * gcm_key, int gcm_key_len,  // key
    unsigned char * gcm_iv, size_t gcm_iv_len,  // initialization vector
    unsigned char * gcm_tag, int gcm_tag_len,  // authentication tag
    unsigned char * gcm_aad, int gcm_aad_len,  // additional authenticated data
    int debug  // 0 (no debug) or 1 (debug)
) {
    int i = 0;
    EVP_CIPHER_CTX *ctx;
    EVP_CIPHER *cipher = NULL;
    int outlen, rv;
    unsigned char outbuf[1024];
    unsigned char *ptr;
    
    if (debug) {
        printf("AES GCM Decrypt:\n\n");
    }

    if (debug) {
        printf("IV:\n");
        BIO_dump_fp(stdout, gcm_iv, gcm_iv_len);
        printf("\nIV length: %ld\n", gcm_iv_len);
    }

    OSSL_PARAM params[2] = {
        OSSL_PARAM_END, OSSL_PARAM_END
    };

    if (debug) {
        printf("\ngcm_ct Ciphertext:\n");
        BIO_dump_fp(stdout, gcm_ct, gcm_ct_len);
    }

    /* Create a context for the decrypt operation */
    if ((ctx = EVP_CIPHER_CTX_new()) == NULL)
        goto err;

    /* Fetch the cipher implementation */
    if ((cipher = EVP_CIPHER_fetch(libctx, "AES-128-GCM", propq)) == NULL)
        goto err;

    /* Initialize decrypt operation */
    if (!EVP_DecryptInit_ex(ctx, cipher, NULL, NULL, NULL))
        goto err;

    /* Set IV length if different from default 12 bytes (96 bits) */
    if (gcm_iv_len != 12) {
        if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, gcm_iv_len, NULL))
            goto err;
    }

    /* Specify key and IV */
    if (!EVP_DecryptInit_ex(ctx, NULL, NULL, gcm_key, gcm_iv))
        goto err;

    /* Zero or one call to specify any AAD */
    if (gcm_aad_len > 0) {
        if (!EVP_DecryptUpdate(ctx, NULL, &outlen, gcm_aad, gcm_aad_len))
            goto err;
        
        if (debug) {
            printf("\ngcm_aad AAD:\n");
            BIO_dump_fp(stdout, gcm_aad, gcm_aad_len);
        }
    }

    /* Decrypt ciphertext */
    if (!EVP_DecryptUpdate(ctx, outbuf, &outlen, gcm_ct, gcm_ct_len))
        goto err;

    if (debug) {
        printf("\ngcm_tag Tag:\n");
        BIO_dump_fp(stdout, gcm_tag, gcm_tag_len);
    }

    /* Set expected tag value */
    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_TAG, gcm_tag_len, gcm_tag))
        goto err;

    /* Finalize: verify tag */
    rv = EVP_DecryptFinal_ex(ctx, outbuf + outlen, &i);

    /* Check tag verification result */
    if (rv > 0) {
        outlen += i;
        
        if (debug) {
            printf("Tag verify successful!\nPlaintext:\n");
            BIO_dump_fp(stdout, outbuf, outlen);
        }
        
        ptr = text_buf;
        for (i = 0; i < outlen; i++) {
            ptr += sprintf(ptr, "%02X", outbuf[i]);
        }
            
        EVP_CIPHER_free(cipher);
        EVP_CIPHER_CTX_free(ctx);
        return text_buf;
    } else {
        if (debug) {
            printf("Tag verify failed!\nPlaintext not available\n");
        }
        goto err;
    }

err:
    if (debug) {
        ERR_print_errors_fp(stderr);
    }

    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);

    return "error";
}

/* AES GCM Encrypt function */
char * aes_gcm_encrypt(
    unsigned char * gcm_pt, int gcm_pt_len,  // plaintext
    unsigned char * gcm_key, int gcm_key_len,  // key
    unsigned char * gcm_iv, size_t gcm_iv_len,  // initialization vector
    int gcm_tag_len,  // desired tag length
    unsigned char * gcm_aad, int gcm_aad_len,  // additional authenticated data
    int debug  // 0 (no debug) or 1 (debug)
) {
    int i = 0;
    EVP_CIPHER_CTX *ctx;
    EVP_CIPHER *cipher = NULL;
    int outlen, tmplen;
    unsigned char outbuf[1024];
    unsigned char outtag[16];
    unsigned char *ptr = text_buf;

    if (debug) {    
        printf("AES GCM Encrypt:\n");
        printf("Plaintext:\n");
        BIO_dump_fp(stdout, gcm_pt, gcm_pt_len);
    }

    /* Create a context for the encrypt operation */
    if ((ctx = EVP_CIPHER_CTX_new()) == NULL)
        goto err;

    /* Fetch the cipher implementation */
    if ((cipher = EVP_CIPHER_fetch(libctx, "AES-128-GCM", propq)) == NULL)
        goto err;

    /* Initialize encrypt operation */
    if (!EVP_EncryptInit_ex(ctx, cipher, NULL, NULL, NULL))
        goto err;

    /* Set IV length if different from default 12 bytes (96 bits) */
    if (gcm_iv_len != 12) {
        if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_SET_IVLEN, gcm_iv_len, NULL))
            goto err;
    }

    /* Specify key and IV */
    if (!EVP_EncryptInit_ex(ctx, NULL, NULL, gcm_key, gcm_iv))
        goto err;

    /* Zero or one call to specify any AAD */
    if (gcm_aad_len > 0) {
        if (!EVP_EncryptUpdate(ctx, NULL, &outlen, gcm_aad, gcm_aad_len))
            goto err;
            
        if (debug) {
            printf("AAD:\n");
            BIO_dump_fp(stdout, gcm_aad, gcm_aad_len);
        }
    }

    /* Encrypt plaintext */
    if (!EVP_EncryptUpdate(ctx, outbuf, &outlen, gcm_pt, gcm_pt_len))
        goto err;

    /* Output encrypted block */
    if (debug) {    
        printf("Ciphertext:\n");
        BIO_dump_fp(stdout, outbuf, outlen);
    }

    for (i = 0; i < outlen; i++) {
        ptr += sprintf(ptr, "%02X", outbuf[i]);
    }
    ptr += sprintf(ptr, " ");

    /* Finalize encryption */
    if (!EVP_EncryptFinal_ex(ctx, outbuf + outlen, &tmplen))
        goto err;
    
    outlen += tmplen;

    /* Get the tag */
    if (!EVP_CIPHER_CTX_ctrl(ctx, EVP_CTRL_GCM_GET_TAG, gcm_tag_len, outtag))
        goto err;

    /* Output tag */
    if (debug) {    
        printf("Tag:\n");
        BIO_dump_fp(stdout, outtag, gcm_tag_len);
    }

    for (i = 0; i < gcm_tag_len; i++) {
        ptr += sprintf(ptr, "%02X", outtag[i]);
    }
    
    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);
    return text_buf;
    
err:
    if (debug) {
        ERR_print_errors_fp(stderr);
    }

    EVP_CIPHER_free(cipher);
    EVP_CIPHER_CTX_free(ctx);

    return "error";
}