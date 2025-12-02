package com.amazon.guardrail

import com.intellij.codeInspection.ProblemHighlightType
import com.intellij.json.psi.JsonFile
import com.intellij.psi.FileViewProvider
import com.intellij.psi.PsiFile
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import org.mockito.Mockito.mock
import org.mockito.kotlin.whenever

class GuardRailDiagnosticMapperTest {

    private lateinit var mapper: GuardRailDiagnosticMapper
    private lateinit var mockFile: PsiFile

    @Before
    fun setup() {
        mapper = GuardRailDiagnosticMapper()
        mockFile = mock(PsiFile::class.java)
    }

    @Test
    fun `mapResults returns empty list for empty JSON`() {
        val result = mapper.mapResults("{}", mockFile)
        assertTrue(result.isEmpty())
    }

    @Test
    fun `mapResults returns empty list for JSON with empty violations`() {
        val cliOutput = """{"non_compliant": {}, "warning": {}}"""
        val result = mapper.mapResults(cliOutput, mockFile)
        assertTrue(result.isEmpty())
    }

    @Test
    fun `mapResults parses single error violation correctly`() {
        val cliOutput = """{
            "non_compliant": {
                "TestRule": [{
                    "check_id": "R001",
                    "message": "Test error",
                    "path": "/properties/test"
                }]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(1, result.size)
        assertEquals("[R001] Test error", result[0].description)
        assertEquals(ProblemHighlightType.ERROR, result[0].highlightType)
        assertEquals("TestRule", result[0].ruleName)
        assertEquals("/properties/test", result[0].violation.path)
    }

    @Test
    fun `mapResults parses single warning violation correctly`() {
        val cliOutput = """{
            "non_compliant": {},
            "warning": {
                "WarningRule": [{
                    "check_id": "W001",
                    "message": "Test warning",
                    "path": "/properties/warn"
                }]
            }
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(1, result.size)
        assertEquals("[W001] Test warning", result[0].description)
        assertEquals(ProblemHighlightType.WARNING, result[0].highlightType)
        assertEquals("WarningRule", result[0].ruleName)
    }

    @Test
    fun `mapResults parses multiple violations from same rule`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule1": [
                    {"check_id": "E001", "message": "Error 1", "path": "/path1"},
                    {"check_id": "E002", "message": "Error 2", "path": "/path2"}
                ]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(2, result.size)
        assertEquals("[E001] Error 1", result[0].description)
        assertEquals("[E002] Error 2", result[1].description)
    }

    @Test
    fun `mapResults parses violations from multiple rules`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule1": [{"check_id": "E001", "message": "Error 1", "path": "/p1"}],
                "Rule2": [{"check_id": "E002", "message": "Error 2", "path": "/p2"}]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(2, result.size)
        assertTrue(result.any { it.ruleName == "Rule1" })
        assertTrue(result.any { it.ruleName == "Rule2" })
    }

    @Test
    fun `mapResults parses both errors and warnings`() {
        val cliOutput = """{
            "non_compliant": {
                "ErrorRule": [{"check_id": "E001", "message": "Error", "path": "/e"}]
            },
            "warning": {
                "WarnRule": [{"check_id": "W001", "message": "Warning", "path": "/w"}]
            }
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(2, result.size)
        val errors = result.filter { it.highlightType == ProblemHighlightType.ERROR }
        val warnings = result.filter { it.highlightType == ProblemHighlightType.WARNING }
        assertEquals(1, errors.size)
        assertEquals(1, warnings.size)
    }

    @Test
    fun `mapResults handles missing fields in violation`() {
        val cliOutput = """{
            "non_compliant": {
                "Rule": [{"check_id": "E001"}]
            },
            "warning": {}
        }"""

        val result = mapper.mapResults(cliOutput, mockFile)

        assertEquals(1, result.size)
        assertEquals("[E001] ", result[0].description)
    }

    @Test
    fun `extractLineNumber returns 0 for non-JsonFile`() {
        val lineNumber = mapper.extractLineNumber("/properties/test", mockFile)
        assertEquals(0, lineNumber)
    }

    @Test
    fun `extractLineNumber returns 0 for empty path`() {
        val lineNumber = mapper.extractLineNumber("", mockFile)
        assertEquals(0, lineNumber)
    }

    @Test
    fun `extractLineNumber returns 0 when document is null`() {
        val mockJsonFile = mock(JsonFile::class.java)
        val mockViewProvider = mock(FileViewProvider::class.java)

        whenever(mockJsonFile.viewProvider).thenReturn(mockViewProvider)
        whenever(mockViewProvider.document).thenReturn(null)

        val lineNumber = mapper.extractLineNumber("/properties/test", mockJsonFile)
        assertEquals(0, lineNumber)
    }
}
