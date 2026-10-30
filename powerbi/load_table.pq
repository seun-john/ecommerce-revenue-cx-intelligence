// Create a Text parameter named ExportFolder (absolute path to powerbi\exports).
// Create a blank query named LoadTable, then paste this function.
// Each table query calls, e.g., = LoadTable("FactOrders")
(TableName as text) as table =>
let
    Source = Csv.Document(File.Contents(ExportFolder & "\" & TableName & ".csv"),
        [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    Headers
