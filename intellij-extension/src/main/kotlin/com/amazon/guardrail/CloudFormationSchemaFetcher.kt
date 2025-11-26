package com.amazon.guardrail

import com.google.gson.JsonParser
import com.intellij.openapi.diagnostic.Logger
import software.amazon.awssdk.regions.Region
import software.amazon.awssdk.services.cloudformation.CloudFormationClient
import software.amazon.awssdk.services.cloudformation.model.DescribeTypeRequest
import java.io.File

/**
 * Fetches CloudFormation resource type schemas using the AWS CloudFormation API.
 * This class reads the typeName from a local schema file and uses the CloudFormation
 * DescribeType API to fetch the registered schema from AWS.
 */
class CloudFormationSchemaFetcher(
    private val clientFactory: (Region) -> CloudFormationClient = { region ->
        CloudFormationClient.builder().region(region).build()
    }
) {

    private val LOG = Logger.getInstance(CloudFormationSchemaFetcher::class.java)

    // Fetches the schema for a resource type from CloudFormation.
    fun fetchSchema(schemaFilePath: String, region: String = "us-east-1"): String? {
        LOG.info("Fetching schema from CloudFormation | File: $schemaFilePath | Region: $region")
        try {
            val typeName = extractTypeName(schemaFilePath)
            val typeNameArn = typeName?.replace("::", "-")
            if (typeName == null) {
                LOG.error("Failed to extract typeName from schema file: $schemaFilePath")
                return null
            }
            val cfnClient = clientFactory(Region.of(region))

            val request = DescribeTypeRequest.builder()
                .arn("arn:aws:cloudformation:us-east-1::type/resource/$typeNameArn")
                .build()

            LOG.info("Calling CloudFormation DescribeType API for: $typeName")

            val response = cfnClient.describeType(request)
            val schema = response.schema()

            if (schema != null) {
                LOG.info("Successfully fetched schema from CloudFormation | Length: ${schema.length}")
                return schema
            } else {
                LOG.warn("DescribeType returned null schema for: $typeName")
                return null
            }
        } catch (e: Exception) {
            LOG.error("Error fetching schema from CloudFormation", e)
            return null
        }
    }

    internal fun extractTypeName(filePath: String): String? {
        return try {
            val fileContent = File(filePath).readText()
            val jsonObject = JsonParser.parseString(fileContent).asJsonObject

            if (jsonObject.has("typeName")) {
                jsonObject.get("typeName").asString
            } else {
                LOG.warn("Schema file does not contain 'typeName' field: $filePath")
                null
            }
        } catch (e: Exception) {
            LOG.error("Error reading typeName from file: $filePath", e)
            null
        }
    }
}
