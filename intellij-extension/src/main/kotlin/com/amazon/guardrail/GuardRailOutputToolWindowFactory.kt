package com.amazon.guardrail

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.ToolWindow
import com.intellij.openapi.wm.ToolWindowFactory
import com.intellij.ui.content.ContentFactory
import javax.swing.JScrollPane
import javax.swing.JTextArea

/**
 * Factory class for creating the Guard Rail Output tool window.
 * 
 * This factory creates a tool window that displays command execution results
 * including command output, timestamps, and error information.
 */
class GuardRailOutputToolWindowFactory : ToolWindowFactory {
    
    companion object {
        // store panel instances per project
        private val panels = mutableMapOf<Project, GuardRailOutputPanel>()
        
        fun getOutputPanel(project: Project): GuardRailOutputPanel? {
            return panels[project]
        }
    }
    
    override fun createToolWindowContent(project: Project, toolWindow: ToolWindow) {
        val outputPanel = GuardRailOutputPanel(project)
        panels[project] = outputPanel
        
        val content = ContentFactory.getInstance().createContent(
            outputPanel.getComponent(),
            "",
            false
        )
        toolWindow.contentManager.addContent(content)
    }
}
