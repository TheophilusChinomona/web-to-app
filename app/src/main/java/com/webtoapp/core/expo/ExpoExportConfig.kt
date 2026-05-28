package com.webtoapp.core.expo

data class ExpoExportConfig(
    val bundleIdentifier: String = "com.example.myapp",
    val expoSdkVersion: String = "51",
    val targetAndroid: Boolean = true,
    val targetIos: Boolean = true,
    val easProjectId: String? = null
)
