# delta-rs-in-predicate-mre
Simple project to demonstrate an issue

## Issue
There are two issues demonstrated in this project:
- When querying with a predicate that uses an `IN` clause, the clause is ignored and all files for the "parent" partition are requested
- When querying with a predicate that uses an `=` clause, sometimes an extra partition is loaded that does not match the clause criteria

## Expected behaviour
- When querying with a predicate that uses an `IN` clause, only the for partitions matching all clauses are requested from S3
- When querying with a predicate that uses an `=` clause, only the files for the partition matching the clause are requested from S3

## Steps to reproduce
1. Clone this repo
2. Start localstack with `docker-compose up`. The localstack logs should be visible in the terminal.
3. In a separate terminal, load the python script `python -i python/mre.py`. The initial script load will populate the table
4. Execute `upsert(table_name, first_update_frame, use_equals=True)`
5. Note that after the first execution, the S3 objects requested include files in the expected partition but also in 
   another unexpected partition. The second unexpected partition is non-deterministic and may change between executions
   but there is always one unexpected partition.
6. Execute `upsert(table_name, first_update_frame, use_equals=True)` again - note that the unexpected partition is no longer present
7. Execute `upsert(table_name, first_update_frame, use_equals=False)` - this usage of the `IN (..)` clause is ignored, and the files
   requested include all files for the month, effectively ignoring the predicate component for the `partition_day` column.

## Example execution logs

### Python interactive session
```
>>> upsert(table_name, first_update_frame, use_equals=True)
Predicate: source.id = target.id AND source.partition_year=target.partition_year AND source.partition_month=target.partition_month AND source.partition_day=target.partition_day AND target.partition_year = '2024' AND target.partition_month = '07' AND target.partition_day = '31'
>>> upsert(table_name, first_update_frame, use_equals=True)
Predicate: source.id = target.id AND source.partition_year=target.partition_year AND source.partition_month=target.partition_month AND source.partition_day=target.partition_day AND target.partition_year = '2024' AND target.partition_month = '07' AND target.partition_day = '31'
>>> upsert(table_name, first_update_frame, use_equals=False)
Predicate: source.id = target.id AND source.partition_year=target.partition_year AND source.partition_month=target.partition_month AND source.partition_day=target.partition_day AND target.partition_year = '2024' AND target.partition_month = '07' AND target.partition_day IN ('31')
```

### First upsert
```bash
localstack-1  | 2024-07-30T23:16:48.866 DEBUG --- [ asgi_gw_437] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_last_checkpoint
localstack-1  | 2024-07-30T23:16:48.885  INFO --- [ asgi_gw_437] localstack.request.aws     : AWS s3.GetObject => 404 (NoSuchKey)
localstack-1  | 2024-07-30T23:16:48.901 DEBUG --- [ asgi_gw_468] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000000
localstack-1  | 2024-07-30T23:16:48.945  INFO --- [ asgi_gw_468] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
localstack-1  | 2024-07-30T23:16:48.952 DEBUG --- [ asgi_gw_269] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:16:48.952 DEBUG --- [ asgi_gw_428] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:16:48.955  INFO --- [ asgi_gw_269] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:48.957  INFO --- [ asgi_gw_428] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:48.977 DEBUG --- [ asgi_gw_491] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:16:48.978 DEBUG --- [ asgi_gw_449] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:16:48.980  INFO --- [ asgi_gw_491] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:48.981  INFO --- [ asgi_gw_449] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:49.004 DEBUG --- [ asgi_gw_450] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D12/partition_day%3D15/part-00001-7f5077c6-af6c-47e4-ac6a-6a11d97e8cd9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.006  INFO --- [ asgi_gw_450] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:49.009 DEBUG --- [ asgi_gw_405] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D12/partition_day%3D15/part-00001-7f5077c6-af6c-47e4-ac6a-6a11d97e8cd9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.011  INFO --- [ asgi_gw_405] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:49.031 DEBUG --- [ asgi_gw_206] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.034  INFO --- [ asgi_gw_206] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:49.041 DEBUG --- [ asgi_gw_475] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.043  INFO --- [ asgi_gw_475] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:49.050 DEBUG --- [ asgi_gw_359] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.052  INFO --- [ asgi_gw_359] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:49.060 DEBUG --- [ asgi_gw_453] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:49.062  INFO --- [ asgi_gw_453] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:16:49.067 DEBUG --- [ asgi_gw_314] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_73badf92-1fde-49d0-b033-56cccea2790f.json.tmp
localstack-1  | 2024-07-30T23:16:49.068  INFO --- [ asgi_gw_314] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:16:49.072 DEBUG --- [ asgi_gw_455] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:49.109  INFO --- [ asgi_gw_455] localstack.request.aws     : AWS dynamodb.PutItem => 200
localstack-1  | 2024-07-30T23:16:49.114 DEBUG --- [   asgi_gw_1] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000002.json
localstack-1  | 2024-07-30T23:16:49.115  INFO --- [   asgi_gw_1] localstack.request.aws     : AWS s3.CopyObject => 200
localstack-1  | 2024-07-30T23:16:49.119 DEBUG --- [ asgi_gw_427] rolo.gateway.wsgi          : DELETE localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_73badf92-1fde-49d0-b033-56cccea2790f.json.tmp
localstack-1  | 2024-07-30T23:16:49.121  INFO --- [ asgi_gw_427] localstack.request.aws     : AWS s3.DeleteObject => 204
localstack-1  | 2024-07-30T23:16:49.125 DEBUG --- [ asgi_gw_444] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:49.135  INFO --- [ asgi_gw_444] localstack.request.aws     : AWS dynamodb.UpdateItem => 200
localstack-1  | 2024-07-30T23:16:49.140 DEBUG --- [ asgi_gw_481] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:49.145  INFO --- [ asgi_gw_481] localstack.request.aws     : AWS dynamodb.Query => 200
localstack-1  | 2024-07-30T23:16:49.149 DEBUG --- [  asgi_gw_36] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000003
localstack-1  | 2024-07-30T23:16:49.153  INFO --- [  asgi_gw_36] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
localstack-1  | 2024-07-30T23:16:51.472 DEBUG --- [  asgi_gw_49] rolo.gateway.wsgi          : GET localhost.localstack.cloud:4566/_localstack/health
```

Second upsert:
```bash
localstack-1  | 2024-07-30T23:16:57.627 DEBUG --- [ asgi_gw_129] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_last_checkpoint
localstack-1  | 2024-07-30T23:16:57.631  INFO --- [ asgi_gw_129] localstack.request.aws     : AWS s3.GetObject => 404 (NoSuchKey)
localstack-1  | 2024-07-30T23:16:57.639 DEBUG --- [  asgi_gw_92] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000000
localstack-1  | 2024-07-30T23:16:57.643  INFO --- [  asgi_gw_92] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
localstack-1  | 2024-07-30T23:16:57.653 DEBUG --- [ asgi_gw_466] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:16:57.655 DEBUG --- [ asgi_gw_478] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:16:57.658  INFO --- [ asgi_gw_478] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.659  INFO --- [ asgi_gw_466] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.659 DEBUG --- [ asgi_gw_447] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000002.json
localstack-1  | 2024-07-30T23:16:57.665  INFO --- [ asgi_gw_447] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.675 DEBUG --- [ asgi_gw_108] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000002.json
localstack-1  | 2024-07-30T23:16:57.676 DEBUG --- [ asgi_gw_113] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:16:57.678 DEBUG --- [  asgi_gw_28] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:16:57.679  INFO --- [  asgi_gw_28] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.680  INFO --- [ asgi_gw_108] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.682  INFO --- [ asgi_gw_113] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:16:57.703 DEBUG --- [ asgi_gw_457] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.704  INFO --- [ asgi_gw_457] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.708 DEBUG --- [ asgi_gw_416] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.709  INFO --- [ asgi_gw_416] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.728 DEBUG --- [ asgi_gw_472] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.728 DEBUG --- [ asgi_gw_417] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.729  INFO --- [ asgi_gw_472] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.730  INFO --- [ asgi_gw_417] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.735 DEBUG --- [ asgi_gw_492] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.735 DEBUG --- [ asgi_gw_231] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.736  INFO --- [ asgi_gw_231] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.737  INFO --- [ asgi_gw_492] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.742 DEBUG --- [ asgi_gw_473] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-293187b9-d32e-4295-923b-6371e5ad08d4-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.742 DEBUG --- [ asgi_gw_432] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.743  INFO --- [ asgi_gw_432] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.744  INFO --- [ asgi_gw_473] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:16:57.749 DEBUG --- [  asgi_gw_62] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-d28e5706-7999-4e6b-8529-3d9105ca4bef-c000.snappy.parquet
localstack-1  | 2024-07-30T23:16:57.750  INFO --- [  asgi_gw_62] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:16:57.753 DEBUG --- [  asgi_gw_14] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_2750513c-3385-4645-9389-fbcfb86ee9db.json.tmp
localstack-1  | 2024-07-30T23:16:57.754  INFO --- [  asgi_gw_14] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:16:57.757 DEBUG --- [   asgi_gw_8] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:57.767  INFO --- [   asgi_gw_8] localstack.request.aws     : AWS dynamodb.PutItem => 200
localstack-1  | 2024-07-30T23:16:57.771 DEBUG --- [ asgi_gw_479] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000003.json
localstack-1  | 2024-07-30T23:16:57.772  INFO --- [ asgi_gw_479] localstack.request.aws     : AWS s3.CopyObject => 200
localstack-1  | 2024-07-30T23:16:57.776 DEBUG --- [ asgi_gw_467] rolo.gateway.wsgi          : DELETE localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_2750513c-3385-4645-9389-fbcfb86ee9db.json.tmp
localstack-1  | 2024-07-30T23:16:57.777  INFO --- [ asgi_gw_467] localstack.request.aws     : AWS s3.DeleteObject => 204
localstack-1  | 2024-07-30T23:16:57.780 DEBUG --- [  asgi_gw_53] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:57.788  INFO --- [  asgi_gw_53] localstack.request.aws     : AWS dynamodb.UpdateItem => 200
localstack-1  | 2024-07-30T23:16:57.794 DEBUG --- [ asgi_gw_499] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:16:57.797  INFO --- [ asgi_gw_499] localstack.request.aws     : AWS dynamodb.Query => 200
localstack-1  | 2024-07-30T23:16:57.800 DEBUG --- [ asgi_gw_531] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000004
localstack-1  | 2024-07-30T23:16:57.803  INFO --- [ asgi_gw_531] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
```

Upsert with `IN` clause:
```bash
localstack-1  | 2024-07-30T23:18:57.045 DEBUG --- [ asgi_gw_151] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_last_checkpoint
localstack-1  | 2024-07-30T23:18:57.058  INFO --- [ asgi_gw_151] localstack.request.aws     : AWS s3.GetObject => 404 (NoSuchKey)
localstack-1  | 2024-07-30T23:18:57.065 DEBUG --- [ asgi_gw_282] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000000
localstack-1  | 2024-07-30T23:18:57.080  INFO --- [ asgi_gw_282] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
localstack-1  | 2024-07-30T23:18:57.095 DEBUG --- [ asgi_gw_353] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000004.json
localstack-1  | 2024-07-30T23:18:57.095 DEBUG --- [ asgi_gw_175] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:18:57.096 DEBUG --- [ asgi_gw_140] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000002.json
localstack-1  | 2024-07-30T23:18:57.097 DEBUG --- [ asgi_gw_138] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:18:57.097 DEBUG --- [  asgi_gw_13] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000003.json
localstack-1  | 2024-07-30T23:18:57.101  INFO --- [ asgi_gw_175] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.101  INFO --- [ asgi_gw_138] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.102  INFO --- [ asgi_gw_353] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.103  INFO --- [  asgi_gw_13] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.104  INFO --- [ asgi_gw_140] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.120 DEBUG --- [ asgi_gw_263] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000001.json
localstack-1  | 2024-07-30T23:18:57.120 DEBUG --- [  asgi_gw_12] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000002.json
localstack-1  | 2024-07-30T23:18:57.122 DEBUG --- [ asgi_gw_118] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000003.json
localstack-1  | 2024-07-30T23:18:57.123 DEBUG --- [ asgi_gw_240] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000004.json
localstack-1  | 2024-07-30T23:18:57.124 DEBUG --- [ asgi_gw_169] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000000.json
localstack-1  | 2024-07-30T23:18:57.125  INFO --- [  asgi_gw_12] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.126  INFO --- [ asgi_gw_169] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.127  INFO --- [ asgi_gw_263] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.127  INFO --- [ asgi_gw_240] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.128  INFO --- [ asgi_gw_118] localstack.request.aws     : AWS s3.GetObject => 200
localstack-1  | 2024-07-30T23:18:57.177 DEBUG --- [ asgi_gw_270] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-f767c6a8-9191-4bd9-b676-b06acddd5492-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.179  INFO --- [ asgi_gw_270] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.184 DEBUG --- [ asgi_gw_168] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-f767c6a8-9191-4bd9-b676-b06acddd5492-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.185  INFO --- [ asgi_gw_168] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.234 DEBUG --- [ asgi_gw_150] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D20/part-00001-f4c96c08-6f85-486b-8a1a-3fafffcec9ee-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.235 DEBUG --- [ asgi_gw_124] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D15/part-00001-c3cad736-d4db-4246-b255-9a7f540b65ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.236 DEBUG --- [ asgi_gw_542] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D26/part-00001-8ddbd463-3ba4-4785-8bca-a06d903a6c3b-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.237 DEBUG --- [ asgi_gw_517] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D16/part-00001-30a0c722-2a71-4de7-9b24-b1840f337a72-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.238  INFO --- [ asgi_gw_150] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.239  INFO --- [ asgi_gw_124] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.239 DEBUG --- [ asgi_gw_114] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D07/part-00001-b33b3f6b-69ac-4c57-9edf-72761f94be6e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.239 DEBUG --- [ asgi_gw_540] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D25/part-00001-659240b4-47a8-4a73-89ba-9d55f43f40d9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.240  INFO --- [ asgi_gw_542] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.240 DEBUG --- [ asgi_gw_296] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D05/part-00001-289058de-f6fe-4f46-8b74-9727f167e36e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.241 DEBUG --- [  asgi_gw_91] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D18/part-00001-1eff9495-240b-45e1-89cf-c6ff457e6f7d-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.241 DEBUG --- [ asgi_gw_124] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D29/part-00001-8c1de291-2c9e-42e7-86ba-f53c6483aa9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.241 DEBUG --- [  asgi_gw_61] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D19/part-00001-c7160173-7ebf-44ed-b941-46f61904bbb7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.241 DEBUG --- [ asgi_gw_150] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D03/part-00001-cffbb99d-25ef-4407-98fd-e0e1183def14-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.241  INFO --- [ asgi_gw_114] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.242  INFO --- [ asgi_gw_517] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.249 DEBUG --- [ asgi_gw_544] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D13/part-00001-192c2912-101a-4543-89b8-5813b798a520-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.250 DEBUG --- [  asgi_gw_94] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D21/part-00001-baf346e4-5a71-41c1-a24d-f3685364df66-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.243 DEBUG --- [ asgi_gw_288] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.243 DEBUG --- [ asgi_gw_406] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D12/part-00001-478781f4-f987-414a-801f-2786fc75b413-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.244 DEBUG --- [ asgi_gw_131] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D02/part-00001-b4084d4e-6dc5-47eb-ad71-dfb5dea85b82-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.244 DEBUG --- [ asgi_gw_103] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D14/part-00001-c6773f53-3a47-41b2-9f9c-5642670c7710-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.244 DEBUG --- [ asgi_gw_254] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D06/part-00001-47774c25-7c7d-48c2-ace4-e20dab8474ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.245 DEBUG --- [ asgi_gw_112] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D22/part-00001-687311e4-ff11-4eeb-ab68-6ec3fd7552a9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.253 DEBUG --- [ asgi_gw_304] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D04/part-00001-e0192eaa-7142-492d-bc89-20f6af779e80-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.246 DEBUG --- [ asgi_gw_173] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D11/part-00001-954b2f1d-38e6-4251-a7c4-69ceaca27f9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.242 DEBUG --- [ asgi_gw_143] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D23/part-00001-680355b8-69d4-407a-9f50-a7f725c140d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.243  INFO --- [ asgi_gw_540] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.250 DEBUG --- [ asgi_gw_158] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D10/part-00001-7094913e-cb00-48ce-9365-ada35a90e9d2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.251 DEBUG --- [ asgi_gw_145] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D24/part-00001-b1ae30dc-0881-4df5-adc8-90b517add290-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.251 DEBUG --- [ asgi_gw_123] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D09/part-00001-c28a1281-c2f2-407a-840b-f59ee9023282-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.252 DEBUG --- [ asgi_gw_352] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D01/part-00001-b8283179-d080-4755-bbaf-1aaec193b9d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.245 DEBUG --- [ asgi_gw_200] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D28/part-00001-8d6086ec-e512-4b28-a99d-940a2b758ef2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.254 DEBUG --- [ asgi_gw_533] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D27/part-00001-0e0485c8-2af9-4896-a84b-64a75cb240c2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.254 DEBUG --- [ asgi_gw_348] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D17/part-00001-9c07b8bc-64a4-4683-a6e1-18e7b19f49c7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.255 DEBUG --- [ asgi_gw_172] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D30/part-00001-7627c27d-8a2e-4038-bf16-317759f88e0f-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.257  INFO --- [ asgi_gw_296] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.257 DEBUG --- [ asgi_gw_530] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D08/part-00001-21b43e2f-c528-4634-940f-e2a320e38780-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.257 DEBUG --- [ asgi_gw_529] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-f767c6a8-9191-4bd9-b676-b06acddd5492-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.259  INFO --- [  asgi_gw_61] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.260  INFO --- [ asgi_gw_131] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.260  INFO --- [ asgi_gw_143] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.261  INFO --- [ asgi_gw_145] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.261  INFO --- [ asgi_gw_288] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.262  INFO --- [ asgi_gw_150] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.262  INFO --- [ asgi_gw_158] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.262  INFO --- [ asgi_gw_406] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.263  INFO --- [ asgi_gw_103] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.263  INFO --- [ asgi_gw_173] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.264  INFO --- [ asgi_gw_544] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.264  INFO --- [  asgi_gw_91] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.264  INFO --- [ asgi_gw_254] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.265  INFO --- [  asgi_gw_94] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.265  INFO --- [ asgi_gw_112] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.266  INFO --- [ asgi_gw_304] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.268  INFO --- [ asgi_gw_124] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.270  INFO --- [ asgi_gw_123] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.271  INFO --- [ asgi_gw_200] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.272  INFO --- [ asgi_gw_352] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.277  INFO --- [ asgi_gw_533] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.277 DEBUG --- [ asgi_gw_157] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D15/part-00001-c3cad736-d4db-4246-b255-9a7f540b65ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.278 DEBUG --- [ asgi_gw_354] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D20/part-00001-f4c96c08-6f85-486b-8a1a-3fafffcec9ee-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.278  INFO --- [ asgi_gw_348] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.281  INFO --- [ asgi_gw_172] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.282  INFO --- [ asgi_gw_529] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.283  INFO --- [ asgi_gw_530] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.293 DEBUG --- [ asgi_gw_246] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D26/part-00001-8ddbd463-3ba4-4785-8bca-a06d903a6c3b-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.298 DEBUG --- [ asgi_gw_110] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D25/part-00001-659240b4-47a8-4a73-89ba-9d55f43f40d9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.298 DEBUG --- [ asgi_gw_304] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D07/part-00001-b33b3f6b-69ac-4c57-9edf-72761f94be6e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.309 DEBUG --- [ asgi_gw_117] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D16/part-00001-30a0c722-2a71-4de7-9b24-b1840f337a72-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.315  INFO --- [ asgi_gw_110] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.316  INFO --- [ asgi_gw_304] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.317  INFO --- [ asgi_gw_157] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.317  INFO --- [ asgi_gw_354] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.318  INFO --- [ asgi_gw_246] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.323  INFO --- [ asgi_gw_117] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.323 DEBUG --- [ asgi_gw_110] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D19/part-00001-c7160173-7ebf-44ed-b941-46f61904bbb7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.323 DEBUG --- [ asgi_gw_304] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D23/part-00001-680355b8-69d4-407a-9f50-a7f725c140d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.326 DEBUG --- [ asgi_gw_157] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D02/part-00001-b4084d4e-6dc5-47eb-ad71-dfb5dea85b82-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.328 DEBUG --- [ asgi_gw_246] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D05/part-00001-289058de-f6fe-4f46-8b74-9727f167e36e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.328 DEBUG --- [ asgi_gw_153] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D24/part-00001-b1ae30dc-0881-4df5-adc8-90b517add290-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.337  INFO --- [ asgi_gw_110] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.337  INFO --- [ asgi_gw_304] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.338  INFO --- [ asgi_gw_157] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.338 DEBUG --- [ asgi_gw_301] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D03/part-00001-cffbb99d-25ef-4407-98fd-e0e1183def14-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.340  INFO --- [ asgi_gw_246] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.340 DEBUG --- [  asgi_gw_66] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D11/part-00001-954b2f1d-38e6-4251-a7c4-69ceaca27f9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.341 DEBUG --- [ asgi_gw_543] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D12/part-00001-478781f4-f987-414a-801f-2786fc75b413-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.341 DEBUG --- [  asgi_gw_39] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D10/part-00001-7094913e-cb00-48ce-9365-ada35a90e9d2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.342 DEBUG --- [ asgi_gw_192] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.343 DEBUG --- [  asgi_gw_15] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D14/part-00001-c6773f53-3a47-41b2-9f9c-5642670c7710-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.348  INFO --- [ asgi_gw_153] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.350 DEBUG --- [ asgi_gw_252] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D21/part-00001-baf346e4-5a71-41c1-a24d-f3685364df66-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.351 DEBUG --- [  asgi_gw_99] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D18/part-00001-1eff9495-240b-45e1-89cf-c6ff457e6f7d-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.352 DEBUG --- [ asgi_gw_558] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D06/part-00001-47774c25-7c7d-48c2-ace4-e20dab8474ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.353 DEBUG --- [ asgi_gw_261] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D13/part-00001-192c2912-101a-4543-89b8-5813b798a520-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.354  INFO --- [ asgi_gw_301] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.354  INFO --- [  asgi_gw_66] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.358  INFO --- [ asgi_gw_543] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.361  INFO --- [ asgi_gw_192] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.362  INFO --- [  asgi_gw_15] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.362  INFO --- [  asgi_gw_39] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.363 DEBUG --- [ asgi_gw_194] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D04/part-00001-e0192eaa-7142-492d-bc89-20f6af779e80-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.365  INFO --- [ asgi_gw_252] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.367  INFO --- [ asgi_gw_558] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.368  INFO --- [  asgi_gw_99] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.369  INFO --- [ asgi_gw_261] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.372 DEBUG --- [  asgi_gw_39] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D22/part-00001-687311e4-ff11-4eeb-ab68-6ec3fd7552a9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.375  INFO --- [ asgi_gw_194] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.379 DEBUG --- [ asgi_gw_292] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D29/part-00001-8c1de291-2c9e-42e7-86ba-f53c6483aa9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.380 DEBUG --- [ asgi_gw_261] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D09/part-00001-c28a1281-c2f2-407a-840b-f59ee9023282-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.381 DEBUG --- [ asgi_gw_252] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D01/part-00001-b8283179-d080-4755-bbaf-1aaec193b9d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.381 DEBUG --- [ asgi_gw_558] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D28/part-00001-8d6086ec-e512-4b28-a99d-940a2b758ef2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.382 DEBUG --- [  asgi_gw_99] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-f767c6a8-9191-4bd9-b676-b06acddd5492-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.383 DEBUG --- [ asgi_gw_322] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D27/part-00001-0e0485c8-2af9-4896-a84b-64a75cb240c2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.384 DEBUG --- [  asgi_gw_16] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D17/part-00001-9c07b8bc-64a4-4683-a6e1-18e7b19f49c7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.386  INFO --- [  asgi_gw_39] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.388 DEBUG --- [ asgi_gw_562] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D08/part-00001-21b43e2f-c528-4634-940f-e2a320e38780-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.389 DEBUG --- [ asgi_gw_142] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D30/part-00001-7627c27d-8a2e-4038-bf16-317759f88e0f-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.391  INFO --- [ asgi_gw_322] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.392  INFO --- [ asgi_gw_558] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.393  INFO --- [ asgi_gw_292] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.393  INFO --- [ asgi_gw_252] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.394  INFO --- [ asgi_gw_261] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.394  INFO --- [  asgi_gw_99] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.395  INFO --- [  asgi_gw_16] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.399 DEBUG --- [ asgi_gw_528] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D20/part-00001-f4c96c08-6f85-486b-8a1a-3fafffcec9ee-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.399 DEBUG --- [ asgi_gw_101] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D25/part-00001-659240b4-47a8-4a73-89ba-9d55f43f40d9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.401 DEBUG --- [ asgi_gw_361] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D07/part-00001-b33b3f6b-69ac-4c57-9edf-72761f94be6e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.401 DEBUG --- [ asgi_gw_144] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D15/part-00001-c3cad736-d4db-4246-b255-9a7f540b65ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.402 DEBUG --- [ asgi_gw_536] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D26/part-00001-8ddbd463-3ba4-4785-8bca-a06d903a6c3b-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.406  INFO --- [ asgi_gw_562] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.407  INFO --- [ asgi_gw_142] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.408 DEBUG --- [ asgi_gw_234] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D16/part-00001-30a0c722-2a71-4de7-9b24-b1840f337a72-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.411  INFO --- [ asgi_gw_361] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.411  INFO --- [ asgi_gw_144] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.412  INFO --- [ asgi_gw_101] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.412  INFO --- [ asgi_gw_528] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.412  INFO --- [ asgi_gw_536] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.421 DEBUG --- [ asgi_gw_101] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D02/part-00001-b4084d4e-6dc5-47eb-ad71-dfb5dea85b82-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.422 DEBUG --- [ asgi_gw_223] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D05/part-00001-289058de-f6fe-4f46-8b74-9727f167e36e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.422 DEBUG --- [ asgi_gw_528] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D19/part-00001-c7160173-7ebf-44ed-b941-46f61904bbb7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.422 DEBUG --- [ asgi_gw_144] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D23/part-00001-680355b8-69d4-407a-9f50-a7f725c140d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.423  INFO --- [ asgi_gw_234] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.423 DEBUG --- [ asgi_gw_361] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D24/part-00001-b1ae30dc-0881-4df5-adc8-90b517add290-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.429  INFO --- [ asgi_gw_101] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.430  INFO --- [ asgi_gw_528] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.431  INFO --- [ asgi_gw_223] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.432  INFO --- [ asgi_gw_144] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.433  INFO --- [ asgi_gw_361] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.436 DEBUG --- [ asgi_gw_442] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D03/part-00001-cffbb99d-25ef-4407-98fd-e0e1183def14-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.437 DEBUG --- [ asgi_gw_273] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D12/part-00001-478781f4-f987-414a-801f-2786fc75b413-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.438 DEBUG --- [ asgi_gw_266] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D11/part-00001-954b2f1d-38e6-4251-a7c4-69ceaca27f9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.439 DEBUG --- [ asgi_gw_262] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-64761a5d-f600-47b8-8b87-6d26b5675a61-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.441 DEBUG --- [  asgi_gw_76] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D14/part-00001-c6773f53-3a47-41b2-9f9c-5642670c7710-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.442 DEBUG --- [ asgi_gw_170] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D10/part-00001-7094913e-cb00-48ce-9365-ada35a90e9d2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.447  INFO --- [ asgi_gw_442] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.448  INFO --- [ asgi_gw_273] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.453 DEBUG --- [ asgi_gw_483] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D06/part-00001-47774c25-7c7d-48c2-ace4-e20dab8474ad-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.455 DEBUG --- [  asgi_gw_77] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D04/part-00001-e0192eaa-7142-492d-bc89-20f6af779e80-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.453 DEBUG --- [ asgi_gw_333] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D21/part-00001-baf346e4-5a71-41c1-a24d-f3685364df66-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.453 DEBUG --- [ asgi_gw_236] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D13/part-00001-192c2912-101a-4543-89b8-5813b798a520-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.454 DEBUG --- [ asgi_gw_209] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D18/part-00001-1eff9495-240b-45e1-89cf-c6ff457e6f7d-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.454  INFO --- [  asgi_gw_76] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.464  INFO --- [ asgi_gw_483] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.453  INFO --- [ asgi_gw_170] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.457  INFO --- [ asgi_gw_262] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.472 DEBUG --- [ asgi_gw_122] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D08/part-00001-21b43e2f-c528-4634-940f-e2a320e38780-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.455  INFO --- [ asgi_gw_266] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.466  INFO --- [  asgi_gw_77] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.467 DEBUG --- [  asgi_gw_75] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D28/part-00001-8d6086ec-e512-4b28-a99d-940a2b758ef2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.469  INFO --- [ asgi_gw_209] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.469 DEBUG --- [ asgi_gw_281] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D29/part-00001-8c1de291-2c9e-42e7-86ba-f53c6483aa9c-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.469 DEBUG --- [ asgi_gw_191] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-f767c6a8-9191-4bd9-b676-b06acddd5492-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.469 DEBUG --- [ asgi_gw_247] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D09/part-00001-c28a1281-c2f2-407a-840b-f59ee9023282-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.470 DEBUG --- [  asgi_gw_76] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D27/part-00001-0e0485c8-2af9-4896-a84b-64a75cb240c2-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.470 DEBUG --- [ asgi_gw_219] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D01/part-00001-b8283179-d080-4755-bbaf-1aaec193b9d5-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.471  INFO --- [ asgi_gw_236] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.471 DEBUG --- [ asgi_gw_483] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D17/part-00001-9c07b8bc-64a4-4683-a6e1-18e7b19f49c7-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.471 DEBUG --- [ asgi_gw_170] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D30/part-00001-7627c27d-8a2e-4038-bf16-317759f88e0f-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.471  INFO --- [ asgi_gw_333] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.464 DEBUG --- [ asgi_gw_319] rolo.gateway.wsgi          : GET localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D22/part-00001-687311e4-ff11-4eeb-ab68-6ec3fd7552a9-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.488  INFO --- [ asgi_gw_319] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.477  INFO --- [  asgi_gw_75] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.481  INFO --- [ asgi_gw_191] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.481  INFO --- [ asgi_gw_247] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.481  INFO --- [ asgi_gw_281] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.483  INFO --- [  asgi_gw_76] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.485  INFO --- [ asgi_gw_219] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.486  INFO --- [ asgi_gw_483] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.487  INFO --- [ asgi_gw_170] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.474  INFO --- [ asgi_gw_122] localstack.request.aws     : AWS s3.GetObject => 206
localstack-1  | 2024-07-30T23:18:57.514 DEBUG --- [ asgi_gw_295] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/partition_year%3D2024/partition_month%3D07/partition_day%3D31/part-00001-32b79b76-f80a-4ac8-8cec-caa15695910e-c000.snappy.parquet
localstack-1  | 2024-07-30T23:18:57.517  INFO --- [ asgi_gw_295] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:18:57.522 DEBUG --- [ asgi_gw_294] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_3d688b79-284b-4074-a840-4e673f48a1d7.json.tmp
localstack-1  | 2024-07-30T23:18:57.524  INFO --- [ asgi_gw_294] localstack.request.aws     : AWS s3.PutObject => 200
localstack-1  | 2024-07-30T23:18:57.530 DEBUG --- [ asgi_gw_277] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:18:57.663  INFO --- [ asgi_gw_277] localstack.request.aws     : AWS dynamodb.PutItem => 200
localstack-1  | 2024-07-30T23:18:57.668 DEBUG --- [ asgi_gw_102] rolo.gateway.wsgi          : PUT localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/00000000000000000005.json
localstack-1  | 2024-07-30T23:18:57.671  INFO --- [ asgi_gw_102] localstack.request.aws     : AWS s3.CopyObject => 200
localstack-1  | 2024-07-30T23:18:57.676 DEBUG --- [  asgi_gw_43] rolo.gateway.wsgi          : DELETE localhost:4566/test-bucket/test-table-4fe69566-9112-434a-959f-1b85d1eea52e/_delta_log/_commit_3d688b79-284b-4074-a840-4e673f48a1d7.json.tmp
localstack-1  | 2024-07-30T23:18:57.678  INFO --- [  asgi_gw_43] localstack.request.aws     : AWS s3.DeleteObject => 204
localstack-1  | 2024-07-30T23:18:57.683 DEBUG --- [ asgi_gw_360] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:18:57.712  INFO --- [ asgi_gw_360] localstack.request.aws     : AWS dynamodb.UpdateItem => 200
localstack-1  | 2024-07-30T23:18:57.718 DEBUG --- [ asgi_gw_148] rolo.gateway.wsgi          : POST localhost:4566/
localstack-1  | 2024-07-30T23:18:57.727  INFO --- [ asgi_gw_148] localstack.request.aws     : AWS dynamodb.Query => 200
localstack-1  | 2024-07-30T23:18:57.731 DEBUG --- [ asgi_gw_132] rolo.gateway.wsgi          : GET localhost:4566/test-bucket?list-type=2&prefix=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F&start-after=test-table-4fe69566-9112-434a-959f-1b85d1eea52e%2F_delta_log%2F00000000000000000006
localstack-1  | 2024-07-30T23:18:57.734  INFO --- [ asgi_gw_132] localstack.request.aws     : AWS s3.ListObjectsV2 => 200
```