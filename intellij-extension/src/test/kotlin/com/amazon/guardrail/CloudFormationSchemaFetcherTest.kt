package com.amazon.guardrail

import org.mockito.Mockito.mock
import org.mockito.kotlin.any
import org.mockito.kotlin.whenever
import org.testng.Assert.assertEquals
import org.testng.Assert.assertNull
import org.testng.annotations.AfterMethod
import org.testng.annotations.BeforeMethod
import org.testng.annotations.Test
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.cloudformation.CloudFormationClient
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeRequest
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeResponse
import java.io.File
import java.nio.file.Files

class CloudFormationSchemaFetcherTest {

    private lateinit var tempDir: File
    private lateinit var mockClient: CloudFormationClient
    private lateinit var fetcher: CloudFormationSchemaFetcher

    @BeforeMethod
    fun setup() {
        tempDir = Files.createTempDirectory("test").toFile()
        mockClient = mock(CloudFormationClient::class.java)
        fetcher = CloudFormationSchemaFetcher { mockClient }
    }

    @AfterMethod
    fun teardown() {
        tempDir.deleteRecursively()
    }

    @Test
    fun `extractTypeName returns null when typeName field is missing`() {
        val file = File(tempDir, "no-typename.json")
        file.writeText("""{"properties": {}}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertNull(result)
    }

    @Test
    fun `extractTypeName extracts typeName from valid schema`() {
        val file = File(tempDir, "valid.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertEquals(result, "AWS::S3::Bucket")
    }

    @Test
    fun `extractTypeName handles complex typeName`() {
        val file = File(tempDir, "complex.json")
        file.writeText("""{"typeName": "AWS::EC2::Instance", "properties": {"foo": "bar"}}""")

        val result = fetcher.extractTypeName(file.absolutePath)
        assertEquals(result, "AWS::EC2::Instance")
    }

    @Test
    fun `fetchSchema returns schema from CloudFormation API`() {
        val file = File(tempDir, "schema.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result = fetcher.fetchSchema(file.absolutePath)

        assertEquals(result, """{"type": "object"}""")
    }

    @Test
    fun `fetchSchema returns null when CloudFormation returns null schema`() {
        val file = File(tempDir, "schema.json")
        file.writeText("""{"typeName": "AWS::Custom::Resource"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn(null)
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result = fetcher.fetchSchema(file.absolutePath)

        assertNull(result)
    }

    @Test
    fun `fetchSchema uses correct region`() {
        val file = File(tempDir, "schema.json")
        file.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        var capturedRegion: Region? = null
        val customFetcher = CloudFormationSchemaFetcher { region ->
            capturedRegion = region
            mockClient
        }

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        customFetcher.fetchSchema(file.absolutePath, "eu-west-1")

        assertEquals(capturedRegion, Region.EU_WEST_1)
    }

    @Test
    fun `fetchSchema handles multiple resource types`() {
        val file1 = File(tempDir, "s3.json")
        file1.writeText("""{"typeName": "AWS::S3::Bucket"}""")

        val file2 = File(tempDir, "ec2.json")
        file2.writeText("""{"typeName": "AWS::EC2::Instance"}""")

        val mockResponse = mock(DescribeTypeResponse::class.java)
        whenever(mockResponse.schema()).thenReturn("""{"type": "object"}""")
        whenever(mockClient.describeType(any<DescribeTypeRequest>())).thenReturn(mockResponse)

        val result1 = fetcher.fetchSchema(file1.absolutePath)
        val result2 = fetcher.fetchSchema(file2.absolutePath)

        assertEquals(result1, """{"type": "object"}""")
        assertEquals(result2, """{"type": "object"}""")
    }
}
