package com.webtoapp.core.expo

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import com.webtoapp.core.logging.AppLogger
import com.webtoapp.data.model.AppType
import com.webtoapp.data.model.WebApp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileInputStream
import java.io.FileOutputStream
import java.util.zip.ZipEntry
import java.util.zip.ZipOutputStream

class ExpoProjectGenerator(private val context: Context) {

    sealed class Result {
        data class Success(val zipFile: File) : Result()
        data class Error(val message: String) : Result()
    }

    suspend fun generate(webApp: WebApp, config: ExpoExportConfig): Result =
        withContext(Dispatchers.IO) {
            try {
                val projectDir = buildProjectDir(webApp, config)
                val zipFile = zipProject(webApp, projectDir)
                projectDir.deleteRecursively()
                Result.Success(zipFile)
            } catch (e: Exception) {
                AppLogger.e("ExpoProjectGenerator", "Generation failed", e)
                Result.Error(e.message ?: "Unknown error")
            }
        }

    private fun buildProjectDir(webApp: WebApp, config: ExpoExportConfig): File {
        val slug = webApp.name.lowercase().replace(Regex("[^a-z0-9]+"), "-").trim('-').ifBlank { "my-app" }
        val packageName = webApp.packageName ?: "com.example.${slug.replace("-", "")}"

        val dir = File(context.cacheDir, "expo_gen_${System.currentTimeMillis()}")
        dir.mkdirs()
        File(dir, "assets").mkdirs()

        // app.json
        File(dir, "app.json").writeText(
            ExpoAppTemplate.appJson(
                appName = webApp.name,
                slug = slug,
                packageName = packageName,
                bundleIdentifier = config.bundleIdentifier.ifBlank { "com.example.$slug" },
                sdkVersion = config.expoSdkVersion
            )
        )

        // package.json
        File(dir, "package.json").writeText(
            ExpoAppTemplate.packageJson(webApp.name, config.expoSdkVersion)
        )

        // babel.config.js
        File(dir, "babel.config.js").writeText(ExpoAppTemplate.babelConfig)

        // tsconfig.json
        File(dir, "tsconfig.json").writeText(ExpoAppTemplate.tsConfig)

        // README.md
        File(dir, "README.md").writeText(ExpoAppTemplate.readme(webApp.name))

        // App.tsx
        File(dir, "App.tsx").writeText(buildAppTsx(webApp))

        // Icon assets
        copyIconAssets(webApp.iconPath, dir)

        return dir
    }

    private fun buildAppTsx(webApp: WebApp): String = when (webApp.appType) {
        AppType.WEB -> ExpoAppTemplate.webView(webApp.url)

        AppType.HTML -> {
            val htmlContent = readHtmlContent(webApp)
            if (htmlContent != null) {
                ExpoAppTemplate.inlineHtml(htmlContent)
            } else {
                ExpoAppTemplate.webView(webApp.url.ifBlank { "about:blank" })
            }
        }

        AppType.FRONTEND -> {
            val htmlContent = readHtmlContent(webApp)
            if (htmlContent != null) {
                ExpoAppTemplate.inlineHtml(htmlContent)
            } else {
                ExpoAppTemplate.webView(webApp.url.ifBlank { "about:blank" })
            }
        }

        AppType.MULTI_WEB -> {
            val multiWebConfig = webApp.multiWebConfig
            if (multiWebConfig != null && multiWebConfig.sites.isNotEmpty()) {
                ExpoAppTemplate.multiWeb(multiWebConfig)
            } else {
                ExpoAppTemplate.webView(webApp.url.ifBlank { "about:blank" })
            }
        }

        AppType.NODEJS_APP, AppType.PHP_APP, AppType.PYTHON_APP, AppType.GO_APP, AppType.WORDPRESS -> {
            val note = "This app runs a local ${webApp.appType.name.lowercase()} server on Android.\n" +
                "For Expo Go, point the WebView at an externally hosted URL, or deploy your backend online."
            ExpoAppTemplate.serverApp(webApp.url.ifBlank { "http://localhost:3000" }, note)
        }

        else -> ExpoAppTemplate.webView(webApp.url.ifBlank { "about:blank" })
    }

    private fun readHtmlContent(webApp: WebApp): String? {
        val htmlConfig = webApp.htmlConfig ?: return null
        val projectDir = htmlConfig.projectDir?.let { File(it) }
        val entryFile = htmlConfig.getValidEntryFile()

        if (projectDir != null && projectDir.exists()) {
            val entry = File(projectDir, entryFile)
            if (entry.exists()) return entry.readText()
        }

        val mainFile = htmlConfig.files.firstOrNull {
            it.name == entryFile || it.name.endsWith("index.html")
        }
        if (mainFile != null) {
            val f = File(mainFile.path)
            if (f.exists()) return f.readText()
        }

        return null
    }

    private fun copyIconAssets(iconPath: String?, dir: File) {
        val assetsDir = File(dir, "assets")
        val iconSizes = mapOf(
            "icon.png" to 1024,
            "adaptive-icon.png" to 1024,
            "splash.png" to 1284
        )

        var sourceBitmap: Bitmap? = null
        if (iconPath != null) {
            val f = File(iconPath)
            if (f.exists()) {
                sourceBitmap = BitmapFactory.decodeFile(f.absolutePath)
            }
        }

        for ((filename, size) in iconSizes) {
            val out = File(assetsDir, filename)
            if (sourceBitmap != null) {
                val scaled = Bitmap.createScaledBitmap(sourceBitmap, size, size, true)
                FileOutputStream(out).use { fos ->
                    scaled.compress(Bitmap.CompressFormat.PNG, 100, fos)
                }
                if (scaled !== sourceBitmap) scaled.recycle()
            } else {
                copyDefaultIcon(out, size)
            }
        }
        sourceBitmap?.recycle()
    }

    private fun copyDefaultIcon(dest: File, size: Int) {
        // White square placeholder — avoids hard-coding an asset dependency
        val bmp = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888)
        bmp.eraseColor(android.graphics.Color.WHITE)
        FileOutputStream(dest).use { bmp.compress(Bitmap.CompressFormat.PNG, 100, it) }
        bmp.recycle()
    }

    private fun zipProject(webApp: WebApp, projectDir: File): File {
        val outDir = context.getExternalFilesDir("expo_projects") ?: context.filesDir
        outDir.mkdirs()

        val safeName = webApp.name.replace(Regex("[^a-zA-Z0-9_-]"), "_")
        val zipFile = File(outDir, "${safeName}_expo.zip")

        ZipOutputStream(FileOutputStream(zipFile)).use { zos ->
            addDirToZip(projectDir, projectDir, zos)
        }

        return zipFile
    }

    private fun addDirToZip(base: File, current: File, zos: ZipOutputStream) {
        current.listFiles()?.forEach { file ->
            val entryName = file.relativeTo(base).path.replace(File.separatorChar, '/')
            if (file.isDirectory) {
                zos.putNextEntry(ZipEntry("$entryName/"))
                zos.closeEntry()
                addDirToZip(base, file, zos)
            } else {
                zos.putNextEntry(ZipEntry(entryName))
                FileInputStream(file).use { it.copyTo(zos) }
                zos.closeEntry()
            }
        }
    }
}
