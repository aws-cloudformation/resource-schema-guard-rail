package com.amazon.guardrail

import com.intellij.notification.Notification
import com.intellij.notification.NotificationType
import com.intellij.notification.Notifications
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.components.service
import com.intellij.openapi.diagnostic.Logger
import com.intellij.openapi.fileTypes.FileTypeManager

/**
 * Action that provides manual validation command for JSON schema files.
 * 
 * This action:
 * - Appears in the editor context menu for JSON files
 * - Can be triggered via keyboard shortcut (Ctrl+Alt+G)
 * - Triggers validation on the currently active file
 * - Shows informational notification when no JSON file is active
 * 
 * Requirements: 4.1, 4.2, 4.3, 4.4, 4.5
 */
class ValidateSchemaAction : AnAction() {
    
    private val LOG = Logger.getInstance(ValidateSchemaAction::class.java)
    
    // action invocation.
    // get the active editor and file
    // call validation service to execute validation
    override fun actionPerformed(e: AnActionEvent) {
        LOG.info("ValidateSchemaAction triggered")
        
        val project = e.project
        if (project == null) {
            LOG.warn("No project available")
            showNotification(
                "Guard Rail Validation",
                "No project is currently open.",
                NotificationType.INFORMATION
            )
            return
        }
        
        // get the active file from the editor
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        if (virtualFile == null) {
            LOG.info("No file is currently active")
            showNotification(
                "Guard Rail Validation",
                "No file is currently active. Open a JSON schema file to validate.",
                NotificationType.INFORMATION
            )
            return
        }
        
        // need to check file extension
        val fileType = FileTypeManager.getInstance().getFileTypeByFile(virtualFile)
        if (fileType.name != "JSON") {
            LOG.info("Active file is not a JSON file: ${virtualFile.name}")
            showNotification(
                "Guard Rail Validation",
                "The active file is not a JSON file. Guard Rail validates JSON schema files only.",
                NotificationType.INFORMATION
            )
            return
        }
        
        LOG.info("Triggering validation for: ${virtualFile.path}")
        
        val validationService = GuardRailValidationService.getInstance()
        validationService.validateFile(virtualFile, project)
        
        showNotification(
            "Guard Rail Validation",
            "Validation started for ${virtualFile.name}",
            NotificationType.INFORMATION
        )
    }
    
    /**
     * Updates the action's enabled/disabled state based on context.
     * 
     * This method:
     * - Enables the action only when a JSON file is active in the editor
     * - Disables the action when no file or non-JSON file is active
     * 
     * Requirements: 4.3
     */
    override fun update(e: AnActionEvent) {
        val project = e.project
        val virtualFile = e.getData(CommonDataKeys.VIRTUAL_FILE)
        
        // Enable action only if:
        //  - project is open
        //  - file is active
        //  - file is a JSON file
        val isEnabled = if (project != null && virtualFile != null) {
            val fileType = FileTypeManager.getInstance().getFileTypeByFile(virtualFile)
            fileType.name == "JSON"
        } else {
            false
        }
        
        e.presentation.isEnabled = isEnabled
        e.presentation.isVisible = true
        
        LOG.debug("Action update: enabled=$isEnabled, file=${virtualFile?.name}")
    }
    
    private fun showNotification(title: String, content: String, type: NotificationType) {
        val notification = Notification(
            "Guard Rail",
            title,
            content,
            type
        )
        Notifications.Bus.notify(notification)
    }
}
