package com.webtoapp.ui.screens

import android.content.Intent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.core.content.FileProvider
import com.webtoapp.core.expo.ExpoExportConfig
import com.webtoapp.core.expo.ExpoProjectGenerator
import com.webtoapp.core.i18n.Strings
import com.webtoapp.data.model.WebApp
import com.webtoapp.ui.components.ThemedBackgroundBox
import kotlinx.coroutines.launch
import org.koin.androidx.compose.koinInject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ExpoExportScreen(
    webApp: WebApp,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val generator: ExpoProjectGenerator = koinInject()
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }

    var bundleId by remember { mutableStateOf(webApp.packageName?.replace("_", ".") ?: "com.example.myapp") }
    var targetAndroid by remember { mutableStateOf(true) }
    var targetIos by remember { mutableStateOf(true) }

    var isGenerating by remember { mutableStateOf(false) }
    var generatedZipPath by remember { mutableStateOf<String?>(null) }

    ThemedBackgroundBox(modifier = Modifier.fillMaxSize()) {
        Scaffold(
            snackbarHost = { SnackbarHost(snackbarHostState) },
            topBar = {
                TopAppBar(
                    title = { Text(Strings.expoExportTitle) },
                    navigationIcon = {
                        IconButton(onClick = onBack) {
                            Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = null)
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
                )
            },
            containerColor = MaterialTheme.colorScheme.background.copy(alpha = 0f)
        ) { padding ->
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 16.dp, vertical = 12.dp),
                verticalArrangement = Arrangement.spacedBy(16.dp)
            ) {
                // Header card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(
                            Icons.Outlined.PhoneAndroid,
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.primary,
                            modifier = Modifier.size(32.dp)
                        )
                        Column {
                            Text(
                                webApp.name,
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                Strings.expoExportDescription,
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.8f)
                            )
                        }
                    }
                }

                // Configuration card
                Card(modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text(
                            Strings.expoTargetPlatforms,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold
                        )

                        Row(
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            FilterChip(
                                selected = targetAndroid,
                                onClick = { if (!targetAndroid || targetIos) targetAndroid = !targetAndroid },
                                label = { Text("Android") },
                                leadingIcon = if (targetAndroid) {
                                    { Icon(Icons.Outlined.Check, null, modifier = Modifier.size(16.dp)) }
                                } else null
                            )
                            FilterChip(
                                selected = targetIos,
                                onClick = { if (!targetIos || targetAndroid) targetIos = !targetIos },
                                label = { Text("iOS") },
                                leadingIcon = if (targetIos) {
                                    { Icon(Icons.Outlined.Check, null, modifier = Modifier.size(16.dp)) }
                                } else null
                            )
                        }

                        HorizontalDivider()

                        Text(
                            Strings.expoBundleId,
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold
                        )
                        OutlinedTextField(
                            value = bundleId,
                            onValueChange = { bundleId = it },
                            modifier = Modifier.fillMaxWidth(),
                            label = { Text("e.g. com.yourcompany.appname") },
                            singleLine = true,
                            textStyle = LocalTextStyle.current.copy(fontFamily = FontFamily.Monospace)
                        )
                    }
                }

                // How-to card
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp),
                        verticalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(6.dp)
                        ) {
                            Icon(Icons.Outlined.Info, null, modifier = Modifier.size(16.dp))
                            Text(Strings.expoHowToRun, style = MaterialTheme.typography.labelMedium, fontWeight = FontWeight.SemiBold)
                        }
                        Text(
                            Strings.expoInstructions,
                            style = MaterialTheme.typography.bodySmall,
                            color = MaterialTheme.colorScheme.onSecondaryContainer.copy(alpha = 0.85f)
                        )
                    }
                }

                // Generate button
                Button(
                    onClick = {
                        scope.launch {
                            isGenerating = true
                            generatedZipPath = null
                            val config = ExpoExportConfig(
                                bundleIdentifier = bundleId.trim().ifBlank { "com.example.myapp" },
                                targetAndroid = targetAndroid,
                                targetIos = targetIos
                            )
                            when (val result = generator.generate(webApp, config)) {
                                is ExpoProjectGenerator.Result.Success -> {
                                    generatedZipPath = result.zipFile.absolutePath
                                    snackbarHostState.showSnackbar(Strings.expoGenerateSuccess)
                                }
                                is ExpoProjectGenerator.Result.Error -> {
                                    snackbarHostState.showSnackbar(
                                        Strings.expoGenerateFailed.replace("%s", result.message)
                                    )
                                }
                            }
                            isGenerating = false
                        }
                    },
                    enabled = !isGenerating && (targetAndroid || targetIos),
                    modifier = Modifier.fillMaxWidth()
                ) {
                    if (isGenerating) {
                        CircularProgressIndicator(
                            modifier = Modifier.size(16.dp),
                            strokeWidth = 2.dp,
                            color = MaterialTheme.colorScheme.onPrimary
                        )
                        Spacer(Modifier.width(8.dp))
                        Text(Strings.expoGenerating)
                    } else {
                        Icon(Icons.Outlined.FileDownload, null, modifier = Modifier.size(18.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(Strings.expoExportTitle)
                    }
                }

                // Success card
                AnimatedVisibility(visible = generatedZipPath != null) {
                    val zipPath = generatedZipPath ?: return@AnimatedVisibility
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.tertiaryContainer)
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            Row(
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(8.dp)
                            ) {
                                Icon(
                                    Icons.Outlined.CheckCircle,
                                    null,
                                    tint = MaterialTheme.colorScheme.tertiary,
                                    modifier = Modifier.size(20.dp)
                                )
                                Text(Strings.expoGenerateSuccess, style = MaterialTheme.typography.titleSmall, fontWeight = FontWeight.SemiBold)
                            }
                            Text(
                                zipPath,
                                style = MaterialTheme.typography.bodySmall,
                                fontFamily = FontFamily.Monospace,
                                color = MaterialTheme.colorScheme.onTertiaryContainer.copy(alpha = 0.7f)
                            )
                            Button(
                                onClick = {
                                    try {
                                        val file = java.io.File(zipPath)
                                        val uri = FileProvider.getUriForFile(
                                            context,
                                            "${context.packageName}.fileprovider",
                                            file
                                        )
                                        val intent = Intent(Intent.ACTION_SEND).apply {
                                            type = "application/zip"
                                            putExtra(Intent.EXTRA_STREAM, uri)
                                            putExtra(Intent.EXTRA_SUBJECT, "${webApp.name} Expo Project")
                                            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                                        }
                                        context.startActivity(Intent.createChooser(intent, Strings.expoShareZip))
                                    } catch (e: Exception) {
                                        scope.launch {
                                            snackbarHostState.showSnackbar(e.message ?: "Share failed")
                                        }
                                    }
                                },
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Icon(Icons.Outlined.Share, null, modifier = Modifier.size(16.dp))
                                Spacer(Modifier.width(6.dp))
                                Text(Strings.expoShareZip)
                            }
                        }
                    }
                }
            }
        }
    }
}
