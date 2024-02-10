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
