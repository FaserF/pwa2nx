#include "updater.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <curl/curl.h>
#include <switch.h>

#include <sys/stat.h>
#include <sys/types.h>
#include "config.h"

#ifdef GITHUB_REPO
#define GITHUB_RELEASE_API "https://api.github.com/repos/" GITHUB_REPO "/releases/latest"
#else
#define GITHUB_RELEASE_API "https://api.github.com/repos/FaserF/pwa2nx/releases/latest"
#endif

#define USER_AGENT "pwa2nx-updater/1.0"

struct MemoryStruct {
    char *memory;
    size_t size;
};

static size_t WriteMemoryCallback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t realsize = size * nmemb;
    struct MemoryStruct *mem = (struct MemoryStruct *)userp;

    char *ptr = realloc(mem->memory, mem->size + realsize + 1);
    if(ptr == NULL) return 0; // out of memory!

    mem->memory = ptr;
    memcpy(&(mem->memory[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->memory[mem->size] = 0;

    return realsize;
}

static size_t WriteFileCallback(void *ptr, size_t size, size_t nmemb, FILE *stream) {
    return fwrite(ptr, size, nmemb, stream);
}

static const char* get_filename(const char* path) {
    const char* filename = path;
    const char* p = path;
    while (*p) {
        if (*p == '/' || *p == '\\') {
            filename = p + 1;
        }
        p++;
    }
    return filename;
}

void check_and_apply_updates(int argc, char* argv[]) {
    CURL *curl_handle;
    CURLcode res;
    struct MemoryStruct chunk;

    chunk.memory = malloc(1);
    chunk.size = 0;

    curl_global_init(CURL_GLOBAL_ALL);
    curl_handle = curl_easy_init();

    if (!curl_handle) {
        free(chunk.memory);
        return;
    }

    curl_easy_setopt(curl_handle, CURLOPT_URL, GITHUB_RELEASE_API);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteMemoryCallback);
    curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, (void *)&chunk);
    curl_easy_setopt(curl_handle, CURLOPT_USERAGENT, USER_AGENT);
    curl_easy_setopt(curl_handle, CURLOPT_TIMEOUT, 15L);
    curl_easy_setopt(curl_handle, CURLOPT_FOLLOWLOCATION, 1L); // Follow redirect
    curl_easy_setopt(curl_handle, CURLOPT_SSL_VERIFYPEER, 0L); // Allow connection on homebrew

    res = curl_easy_perform(curl_handle);

    if(res == CURLE_OK) {
        // Parse the body to find `"tag_name":"vX.Y.Z"`
        char *tag_loc = strstr(chunk.memory, "\"tag_name\":");
        
        if (tag_loc) {
            char version[32] = {0};
            sscanf(tag_loc, "\"tag_name\":\"%[^\"]\"", version);

            // Compare version
            printf("Latest version available: %s\n", version);
            consoleUpdate(NULL);

            // Identify correct asset name based on execution context
            char target_asset[128] = {0};
            const char* running_file = (argc > 0 && argv[0] != NULL) ? get_filename(argv[0]) : NULL;

            if (running_file && strstr(running_file, ".nro")) {
                strncpy(target_asset, running_file, sizeof(target_asset) - 1);
            } else {
#ifdef SAFE_NAME
                snprintf(target_asset, sizeof(target_asset), "%s.nro", SAFE_NAME);
#else
                strncpy(target_asset, "pwa2nx.nro", sizeof(target_asset) - 1);
#endif
            }

            // Find matching asset browser_download_url
            char search_name[256];
            snprintf(search_name, sizeof(search_name), "\"name\":\"%s\"", target_asset);
            char *asset_pos = strstr(chunk.memory, search_name);
            
            // If the specific app build asset doesn't exist in this release, try fallback
            if (!asset_pos) {
                printf("Warning: Asset %s not found. Falling back to universal NRO...\n", target_asset);
                consoleUpdate(NULL);
                
                // Fallback to first .nro asset or default name
                asset_pos = strstr(chunk.memory, ".nro");
                if (asset_pos) {
                    // Try to scan backwards or forward for name boundary
                    char *name_start = strstr(chunk.memory, "\"name\":\"");
                    if (name_start) {
                        sscanf(name_start, "\"name\":\"%[^\"]\"", target_asset);
                        asset_pos = strstr(chunk.memory, name_start);
                    }
                }
            }

            char download_url[512] = {0};
            if (asset_pos) {
                char *url_start = strstr(asset_pos, "\"browser_download_url\":\"");
                if (url_start) {
                    url_start += strlen("\"browser_download_url\":\"");
                    sscanf(url_start, "%[^\"]", download_url);
                }
            }

            if (strlen(download_url) > 0) {
                printf("Downloading update from: %s\n", download_url);
                consoleUpdate(NULL);

                // Determine dynamic write path
                char write_path[512];
                if (argc > 0 && argv[0] != NULL && strncmp(argv[0], "sdmc:", 5) == 0) {
                    strncpy(write_path, argv[0], sizeof(write_path) - 1);
                } else {
#ifdef SAFE_NAME
                    snprintf(write_path, sizeof(write_path), "sdmc:/switch/pwa2nx/%s.nro", SAFE_NAME);
#else
                    snprintf(write_path, sizeof(write_path), "sdmc:/switch/pwa2nx/pwa2nx.nro");
#endif
                }

                // Create directory hierarchy if it doesn't exist
                char dir_path[512];
                snprintf(dir_path, sizeof(dir_path), "%s", write_path);
                char *last_slash = strrchr(dir_path, '/');
                if (last_slash) {
                    *last_slash = '\0';
                    mkdir("sdmc:/switch", 0777);
                    mkdir(dir_path, 0777);
                }

                FILE *fp = fopen(write_path, "wb");
                if (fp) {
                    curl_easy_setopt(curl_handle, CURLOPT_URL, download_url);
                    curl_easy_setopt(curl_handle, CURLOPT_WRITEFUNCTION, WriteFileCallback);
                    curl_easy_setopt(curl_handle, CURLOPT_WRITEDATA, fp);
                    curl_easy_setopt(curl_handle, CURLOPT_TIMEOUT, 60L); // Increase timeout for binary download
                    
                    res = curl_easy_perform(curl_handle);
                    fclose(fp);

                    if (res == CURLE_OK) {
                        printf("Update installed to %s!\nPlease restart the app.\n", get_filename(write_path));
                    } else {
                        printf("Download failed.\n");
                    }
                    consoleUpdate(NULL);
                } else {
                    printf("Failed to open path for writing: %s\n", write_path);
                    consoleUpdate(NULL);
                }
            } else {
                printf("No matching update asset found.\n");
                consoleUpdate(NULL);
            }
        }
    } else {
        printf("Update check failed: %s\n", curl_easy_strerror(res));
        consoleUpdate(NULL);
    }

    curl_easy_cleanup(curl_handle);
    free(chunk.memory);
    curl_global_cleanup();
}
