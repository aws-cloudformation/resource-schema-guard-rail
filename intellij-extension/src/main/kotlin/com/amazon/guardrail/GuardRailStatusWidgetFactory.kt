package com.amazon.guardrail

import com.intellij.openapi.project.Project
import com.intellij.openapi.wm.StatusBar
import com.intellij.openapi.wm.StatusBarWidget
import com.intellij.openapi.wm.StatusBarWidgetFactory

/**
 * Factory for creating GuardRailStatusWidget instances.
 * 
 * This factory is registered in plugin.xml and is responsible for
 * creating and managing the status bar widget for each project.
 */
class GuardRailStatusWidgetFactory : StatusBarWidgetFactory {
    
    /**
     * Returns the unique identifier for this widget factory.
     * Must match the widget ID.
     */
    override fun getId(): String = GuardRailStatusWidget.ID
    
    /**
     * Returns the display name for the widget.
     */
    override fun getDisplayName(): String = "Guard Rail Validation"
    
    /**
     * Returns whether the widget is available for the given project.
     * 
     * The widget is available for all projects.
     */
    override fun isAvailable(project: Project): Boolean = true
    
    /**
     * Creates a new widget instance for the given project.
     * 
     * @param project The project to create the widget for
     * @return A new GuardRailStatusWidget instance
     */
    override fun createWidget(project: Project): StatusBarWidget {
        return GuardRailStatusWidget(project)
    }
    
    /**
     * Disposes the widget for the given project.
     * 
     * @param widget The widget to dispose
     */
    override fun disposeWidget(widget: StatusBarWidget) {
        widget.dispose()
    }
    
    /**
     * Returns whether the widget can be enabled by default.
     */
    override fun canBeEnabledOn(statusBar: StatusBar): Boolean = true
}
