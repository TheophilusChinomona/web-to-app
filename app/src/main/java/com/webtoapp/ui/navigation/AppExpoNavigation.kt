package com.webtoapp.ui.navigation

import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.navigation.NavGraphBuilder
import androidx.navigation.NavHostController
import androidx.navigation.NavType
import androidx.navigation.compose.composable
import androidx.navigation.navArgument
import com.webtoapp.data.model.WebApp
import com.webtoapp.ui.screens.ExpoExportScreen

internal fun NavGraphBuilder.addExpoRoutes(
    navController: NavHostController,
    dependencies: AppNavigationGraphDependencies,
) {
    composable(
        route = Routes.EXPO_EXPORT,
        arguments = listOf(navArgument("appId") { type = NavType.LongType })
    ) { backStackEntry ->
        val appId = backStackEntry.arguments?.getLong("appId") ?: 0L
        var webApp by remember { mutableStateOf<WebApp?>(null) }

        LaunchedEffect(appId) {
            webApp = dependencies.webAppRepository.getWebApp(appId)
        }

        val app = webApp ?: return@composable

        ExpoExportScreen(
            webApp = app,
            onBack = { navController.popBackStack() }
        )
    }
}
