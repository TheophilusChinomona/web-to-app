package com.webtoapp.core.expo

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.Base64
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

        // App.tsx — possibly also writes assets/web.html for static sites
        File(dir, "App.tsx").writeText(buildAppTsxAndAssets(webApp, dir))

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

    private fun buildAppTsxAndAssets(webApp: WebApp, projectDir: File): String {
        if (webApp.appType == AppType.FRONTEND || webApp.appType == AppType.HTML) {
            val htmlConfig = webApp.htmlConfig
            val srcDir = htmlConfig?.projectDir?.let { File(it) }
            val entryFileName = htmlConfig?.getValidEntryFile() ?: "index.html"

            if (srcDir != null && srcDir.exists()) {
                val inlined = inlineStaticSite(srcDir, entryFileName)
                if (inlined != null) {
                    File(projectDir, "assets").mkdirs()
                    File(projectDir, "assets/web.html").writeText(inlined)
                    return ExpoAppTemplate.embeddedHtml()
                }
            }

            val htmlContent = readHtmlContent(webApp)
            return if (htmlContent != null) {
                ExpoAppTemplate.inlineHtml(htmlContent)
            } else {
                ExpoAppTemplate.webView(webApp.url.ifBlank { "about:blank" })
            }
        }
        return buildAppTsx(webApp)
    }

    private fun inlineStaticSite(projectDir: File, entryFileName: String): String? {
        val entryFile = File(projectDir, entryFileName)
        if (!entryFile.exists()) return null

        var html = entryFile.readText()

        // Inline CSS: <link rel="stylesheet" href="..."> → <style>...</style>
        val cssLinkRegex = Regex("""<link\b([^>]*)>""", RegexOption.IGNORE_CASE)
        html = cssLinkRegex.replace(html) { matchResult ->
            val tag = matchResult.value
            val attrs = matchResult.groupValues[1]
            if (!attrs.contains("stylesheet", ignoreCase = true)) return@replace tag
            val href = extractAttrValue(attrs, "href") ?: return@replace tag
            if (isExternalUrl(href)) return@replace tag
            val cssFile = resolveLocalFile(projectDir, href) ?: return@replace tag
            if (!cssFile.exists()) return@replace tag
            val cssContent = inlineCssUrls(cssFile.readText(), cssFile.parentFile ?: projectDir)
            "<style>\n$cssContent\n</style>"
        }

        // Inline JS: <script src="..."></script> → <script>...</script>
        val scriptRegex = Regex("""<script\b([^>]*)>([\s\S]*?)</script>""", RegexOption.IGNORE_CASE)
        html = scriptRegex.replace(html) { matchResult ->
            val attrs = matchResult.groupValues[1]
            val src = extractAttrValue(attrs, "src") ?: return@replace matchResult.value
            if (isExternalUrl(src)) return@replace matchResult.value
            val jsFile = resolveLocalFile(projectDir, src) ?: return@replace matchResult.value
            if (!jsFile.exists()) return@replace matchResult.value
            "<script>\n${jsFile.readText()}\n</script>"
        }

        // Inline images: <img src="..."> → <img src="data:image/...;base64,...">
        val imgSrcRegex = Regex("""(<img\b[^>]*)\bsrc=(["'])([^"']*)\2""", RegexOption.IGNORE_CASE)
        html = imgSrcRegex.replace(html) { matchResult ->
            val prefix = matchResult.groupValues[1]
            val quote = matchResult.groupValues[2]
            val src = matchResult.groupValues[3]
            if (isExternalUrl(src)) return@replace matchResult.value
            val imgFile = resolveLocalFile(projectDir, src) ?: return@replace matchResult.value
            if (!imgFile.exists()) return@replace matchResult.value
            val mimeType = mimeTypeForFile(imgFile)
            val base64 = Base64.encodeToString(imgFile.readBytes(), Base64.NO_WRAP)
            "${prefix}src=${quote}data:$mimeType;base64,$base64${quote}"
        }

        return html
    }

    private fun inlineCssUrls(cssContent: String, cssDir: File): String {
        val urlRegex = Regex("""url\(["']?([^"')]+)["']?\)""", RegexOption.IGNORE_CASE)
        return urlRegex.replace(cssContent) { matchResult ->
            val url = matchResult.groupValues[1]
            if (isExternalUrl(url)) return@replace matchResult.value
            val assetFile = resolveLocalFile(cssDir, url) ?: return@replace matchResult.value
            if (!assetFile.exists()) return@replace matchResult.value
            val mimeType = mimeTypeForFile(assetFile)
            val base64 = Base64.encodeToString(assetFile.readBytes(), Base64.NO_WRAP)
            "url('data:$mimeType;base64,$base64')"
        }
    }

    private fun resolveLocalFile(baseDir: File, path: String): File? {
        if (path.isBlank()) return null
        val cleaned = path.split("?").first().split("#").first()
        return try {
            File(baseDir, cleaned).canonicalFile.takeIf {
                it.absolutePath.startsWith(baseDir.canonicalPath)
            }
        } catch (_: Exception) {
            null
        }
    }

    private fun extractAttrValue(attrs: String, attrName: String): String? {
        val regex = Regex("""\b$attrName=["']([^"']*)["']""", RegexOption.IGNORE_CASE)
        return regex.find(attrs)?.groupValues?.get(1)
    }

    private fun isExternalUrl(url: String): Boolean {
        return url.startsWith("http://") || url.startsWith("https://") ||
               url.startsWith("//") || url.startsWith("data:") || url.startsWith("#")
    }

    private fun mimeTypeForFile(file: File): String = when (file.extension.lowercase()) {
        "png" -> "image/png"
        "jpg", "jpeg" -> "image/jpeg"
        "gif" -> "image/gif"
        "svg" -> "image/svg+xml"
        "webp" -> "image/webp"
        "ico" -> "image/x-icon"
        "woff" -> "font/woff"
        "woff2" -> "font/woff2"
        "ttf" -> "font/ttf"
        "eot" -> "application/vnd.ms-fontobject"
        else -> "application/octet-stream"
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
