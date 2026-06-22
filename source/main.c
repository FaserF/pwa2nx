#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <switch.h>
#include "config.h"

// If no target URL, run in Universal mode
#ifndef TARGET_URL
#define TARGET_URL "https://google.com"
#endif

#ifndef APP_TITLE
#define APP_TITLE "Universal App"
#endif

#ifndef APP_VERSION
#define APP_VERSION "1.0.0"
#endif

#include "updater.h"

// Function prototypes
void launch_web_applet(const char* url, AccountUid* uid, bool has_uid);
bool select_profile(AccountUid* out_uid);

int main(int argc, char* argv[]) {
    // Initialize graphics and console for standard output
    consoleInit(NULL);
    
    printf("\x1b[16;20HInitializing " APP_TITLE " (v" APP_VERSION ")...");
    consoleUpdate(NULL);

    // Check pad state to see if Minus is held on boot to force update check
    padConfigureInput(1, HidNpadStyleSet_NpadStandard);
    PadState pad;
    padInitializeDefault(&pad);
    padUpdate(&pad);
    u64 keys_held = padGetKeysHeld(&pad);

    if (keys_held & HidNpadButton_Minus) {
        printf("\nUpdate check requested...\n");
        consoleUpdate(NULL);
        // Initialize network sockets and check connectivity via NIFM
        u32 ip = 0;
        if (R_SUCCEEDED(nifmInitialize(NifmServiceType_User))) {
            if (R_SUCCEEDED(nifmGetCurrentIpAddress(&ip)) && ip != 0) {
                Result socket_rc = socketInitializeDefault();
                if (R_SUCCEEDED(socket_rc)) {
                    check_and_apply_updates(argc, argv);
                    socketExit();
                }
            }
            nifmExit();
        }
    }


    // Initialize account service
    Result acc_rc = accountInitialize(AccountServiceType_Application);
    AccountUid uid;
    bool has_uid = false;

    if (R_SUCCEEDED(acc_rc)) {
        has_uid = select_profile(&uid);
    }

    char final_url[1024];
    strncpy(final_url, TARGET_URL, sizeof(final_url) - 1);

    // Universal URL Prompt if default URL is not hardcoded/fallback
    if (strcmp(final_url, "https://") == 0 || strcmp(TARGET_URL, "universal") == 0) {
        printf("\n\n\x1b[32mUniversal Mode Enabled\x1b[37m\n");
        printf("Press [A] to enter URL, or [B] to launch default.\n");
        consoleUpdate(NULL);

        // Simple software keyboard input
        SwkbdConfig kbd;
        Result kbd_rc = swkbdCreate(&kbd, 0);
        if (R_SUCCEEDED(kbd_rc)) {
            swkbdConfigMakePresetDefault(&kbd);
            swkbdConfigSetInitialText(&kbd, "https://");
            swkbdConfigSetGuideText(&kbd, "Enter website or PWA URL to launch:");
            
            char input_url[512] = {0};
            kbd_rc = swkbdShow(&kbd, input_url, sizeof(input_url) - 1);
            if (R_SUCCEEDED(kbd_rc) && strlen(input_url) > 0) {
                strncpy(final_url, input_url, sizeof(final_url) - 1);
            }
            swkbdClose(&kbd);
        }
    }

    printf("\nLaunching Web Applet: %s\n", final_url);
    consoleUpdate(NULL);

    launch_web_applet(final_url, &uid, has_uid);

    // Clean up services
    if (R_SUCCEEDED(acc_rc)) {
        accountExit();
    }

    consoleExit(NULL);
    return 0;
}

bool select_profile(AccountUid* out_uid) {
    // Attempt to retrieve preselected user
    if (R_SUCCEEDED(accountGetPreselectedUser(out_uid))) {
        return true;
    }

    // Invoke user selector applet
    PselUserSelectionSettings settings;
    memset(&settings, 0, sizeof(settings));
    if (R_SUCCEEDED(pselShowUserSelector(out_uid, &settings))) {
        return true;
    }

    return false;
}

void launch_web_applet(const char* url, AccountUid* uid, bool has_uid) {
    WebCommonConfig config;
    Result rc = 0;

    // Use regular web page shim
    rc = webPageCreate(&config, url);
    if (R_FAILED(rc)) {
        printf("Failed to create web page configuration: 0x%08X\n", rc);
        consoleUpdate(NULL);
        return;
    }

    // Attach UID for session persistence (cookies, local storage saved to user profile)
    if (has_uid) {
        webConfigSetUid(&config, *uid);
    }

    // Modern wrapper options
    webConfigSetMediaAutoPlay(&config, true);
    webConfigSetWhitelist(&config, "^http.*$"); // Dynamic whitelist allowing all HTTP/S navigation

#if defined(ENABLE_BACKGROUND_PLAYBACK) && ENABLE_BACKGROUND_PLAYBACK == 1
    webConfigSetBootAsMediaPlayer(&config, true);
#endif

    // Execute applet
    WebCommonReply out;
    rc = webConfigShow(&config, &out);
    if (R_FAILED(rc)) {
        printf("Web Applet exited with error code: 0x%08X\n", rc);
        consoleUpdate(NULL);
        // Wait 5 seconds so the user can read the error
        svcSleepThread(5000000000ULL);
    }
}
