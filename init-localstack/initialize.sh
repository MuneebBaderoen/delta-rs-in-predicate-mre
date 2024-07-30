#!/bin/sh

export AWS_DEFAULT_REGION=eu-west-1

awslocal s3api create-bucket --bucket test-bucket --create-bucket-configuration "{\"LocationConstraint\": \"eu-west-1\"}"

awslocal dynamodb create-table \
    --table-name delta-table-lock-provider \
    --attribute-definitions AttributeName=tablePath,AttributeType=S AttributeName=fileName,AttributeType=S \
    --key-schema AttributeName=tablePath,KeyType=HASH AttributeName=fileName,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST

awslocal dynamodb update-time-to-live \
  --table-name delta-table-lock-provider \
  --time-to-live-specification "Enabled=true, AttributeName=expireTime"
