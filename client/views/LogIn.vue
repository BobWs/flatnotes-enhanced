<template>
  <div class="flex h-full flex-col items-center justify-center">
    <Logo class="mb-5" />
    <div v-if="globalStore.config.authType == authTypes.oidc" class="flex max-w-80 flex-col items-center">
      <a v-if="globalStore.config.authProvider == 'github'" href="/api/auth/oidc/login" class="flex items-center gap-2 rounded-md bg-[#24292e] px-5 py-2.5 text-sm font-semibold text-white hover:bg-[#3a3f44] transition-colors">
        <GitHubIcon />
        Continue with GitHub
      </a>
      <a v-else href="/api/auth/oidc/login" class="flex items-center gap-2 rounded-md bg-theme-brand px-5 py-2.5 text-sm font-semibold text-white hover:opacity-90 transition-opacity">
        <OIDCIcon />
        Continue with OIDC
      </a>
    </div>
    <form v-else @submit.prevent="logIn" class="flex max-w-80 flex-col items-center">
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
  </div>
</template>

<script setup>
import { mdilLogin } from "@mdi/light-js";
import { useToast } from "primevue/usetoast";
import { ref } from "vue";
import { useRouter } from "vue-router";

import { apiErrorHandler, getToken } from "../api.js";
import CustomButton from "../components/CustomButton.vue";
import GitHubIcon from "../components/GitHubIcon.vue";
import OIDCIcon from "../components/OIDCIcon.vue";
import Logo from "../components/Logo.vue";
import TextInput from "../components/TextInput.vue";
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