<template>
  <div class="flex h-full flex-col items-center justify-center">
    <Logo class="mb-5" />
    <form @submit.prevent="logIn" class="flex max-w-80 flex-col items-center">
      <TextInput
        v-model="username"
        id="username"
        placeholder="Username"
        class="mb-1"
        autocomplete="username"
        required
      />
      <TextInput
        v-model="password"
        id="password"
        placeholder="Password"
        type="password"
        class="mb-1"
        autocomplete="current-password"
        required
      />
      <TextInput
        v-if="globalStore.config.authType == authTypes.totp"
        v-model="totp"
        id="one-time-code"
        placeholder="2FA Code"
        class="mb-1"
        autocomplete="one-time-code"
        required
      />
      <!-- QR setup link — only visible when TOTP is required -->
      <button
        v-if="globalStore.config.authType == authTypes.totp"
        type="button"
        @click="showTotpModal = true"
        class="mb-2 text-xs text-theme-brand hover:underline self-start"
      >
        <svg viewBox="0 0 24 24" class="w-3 h-3 fill-current inline mr-1">
          <path d="M3,11H5V13H3V11M11,5H13V9H11V5M9,11H13V15H11V13H9V11M15,11H17V13H19V11H21V13H19V15H21V19H19V21H17V19H13V21H11V17H13V15H15V11M19,15H17V19H19V15M15,17H13V19H15V17M5,3H9V7H5V3M3,3H5V5H3V3M5,5H9V7H5V5M13,3H17V7H13V3M11,3H13V5H11V3M13,5H17V7H13V5M3,13H7V17H3V13M5,15H7V17H5V15Z"/>
        </svg>
        Show QR code for authenticator setup
      </button>
      <div class="mb-4 flex">
        <input
          type="checkbox"
          id="remember-me"
          v-model="rememberMe"
          class="mr-1"
        />
        <label for="remember-me">Remember Me</label>
      </div>
      <CustomButton :iconPath="mdilLogin" label="Log In" />
    </form>
    <!-- TOTP setup modal -->
    <TotpSetupModal :show="showTotpModal" @close="showTotpModal = false" />
  </div>
</template>

<script setup>
import { mdilLogin } from "@mdi/light-js";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getToken } from "../api.js";
import CustomButton from "../components/CustomButton.vue";
import Logo from "../components/Logo.vue";
import TextInput from "../components/TextInput.vue";
import TotpSetupModal from "../components/TotpSetupModal.vue";
import { authTypes } from "../constants.js";
import { useGlobalStore } from "../globalStore.js";
import { getToastOptions } from "../helpers.js";
import { storeToken } from "../tokenStorage.js";

const props = defineProps({ redirect: String });

const globalStore = useGlobalStore();
const router = useRouter();
const toast = useToast();

const username = ref("");
const password = ref("");
const totp = ref("");
const rememberMe = ref(false);
const showTotpModal = ref(false);

function logIn() {
  getToken(username.value, password.value, totp.value)
    .then((access_token) => {
      storeToken(access_token, rememberMe.value);
      if (props.redirect) {
        router.push(props.redirect);
      } else {
        router.push({ name: "home" });
      }
    })
    .catch((error) => {
      username.value = "";
      password.value = "";
      totp.value = "";

      if (error.response?.status === 401) {
        toast.add(
          getToastOptions(
            "Please check your credentials and try again.",
            "Login Failed",
            "error",
          ),
        );
      } else {
        apiErrorHandler(error, toast);
      }
    });
}

// Redirect to home if authentication is disabled.
if (globalStore.config.authType === authTypes.none) {
  router.push({ name: "home" });
}
</script>
