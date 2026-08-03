param(
    [string]$Port
)

$ErrorActionPreference = 'Stop'

$powerBiBin = 'C:\Program Files\Microsoft Power BI Desktop\bin'
[System.Reflection.Assembly]::LoadFrom(
    (Join-Path $powerBiBin 'Microsoft.PowerBI.AdomdClient.dll')
) | Out-Null
[System.Reflection.Assembly]::LoadFrom(
    (Join-Path $powerBiBin 'Microsoft.PowerBI.Tabular.dll')
) | Out-Null

if (-not $Port) {
    $workspaceRoot = Join-Path $env:LOCALAPPDATA `
        'Microsoft\Power BI Desktop\AnalysisServicesWorkspaces'
    $portFile = Get-ChildItem -LiteralPath $workspaceRoot -Recurse -File `
        -Filter 'msmdsrv.port.txt' |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if (-not $portFile) {
        throw 'No open Power BI Desktop local model was found.'
    }

    $Port = ((Get-Content -LiteralPath $portFile.FullName -Raw) `
        -replace '[^0-9]', '')
}

$server = [Microsoft.AnalysisServices.Tabular.Server]::new()

function Test-Column {
    param(
        [Microsoft.AnalysisServices.Tabular.Table]$Table,
        [string]$ColumnName
    )

    return $null -ne ($Table.Columns | Where-Object Name -eq $ColumnName)
}

function Set-Measure {
    param(
        [Microsoft.AnalysisServices.Tabular.Table]$Table,
        [string]$Name,
        [string]$Expression,
        [string]$FormatString,
        [string]$DisplayFolder
    )

    $measure = $Table.Measures | Where-Object Name -eq $Name
    if (-not $measure) {
        $measure = [Microsoft.AnalysisServices.Tabular.Measure]::new()
        $measure.Name = $Name
        $Table.Measures.Add($measure)
    }

    $measure.Expression = $Expression
    $measure.FormatString = $FormatString
    $measure.DisplayFolder = $DisplayFolder
}

try {
    $server.Connect("localhost:$Port")
    $database = $server.Databases | Select-Object -First 1
    if (-not $database) {
        throw 'The Power BI local model has no database.'
    }

    $model = $database.Model

    # Correct the two display names only when their columns prove they are swapped.
    $factAcquisition = $model.Tables | Where-Object Name -eq 'FactAcquisition'
    $factSellerLifecycle = $model.Tables |
        Where-Object Name -eq 'FactSellerLifecycle'

    if (
        $factAcquisition -and
        $factSellerLifecycle -and
        (Test-Column $factAcquisition 'activation_status') -and
        (Test-Column $factSellerLifecycle 'total_leads')
    ) {
        $factAcquisition.Name = '__FactSellerLifecycleTemp'
        $factSellerLifecycle.Name = 'FactAcquisition'
        $factAcquisition.Name = 'FactSellerLifecycle'
    }

    $measureTable = $model.Tables | Where-Object Name -eq '_Measures'
    if (-not $measureTable) {
        throw 'The _Measures table was not found.'
    }

    $definitions = @(
        @{
            Name = 'Total Orders'
            Expression = 'DISTINCTCOUNT(FactOrders[order_id])'
            Format = '#,0'
            Folder = 'Commercial'
        },
        @{
            Name = 'GMV'
            Expression = 'SUM(FactOrders[product_value])'
            Format = '"R$" #,0.00'
            Folder = 'Commercial'
        },
        @{
            Name = 'AOV'
            Expression = 'DIVIDE([GMV], [Total Orders])'
            Format = '"R$" #,0.00'
            Folder = 'Commercial'
        },
        @{
            Name = 'Active Sellers'
            Expression = 'DISTINCTCOUNT(FactOrderSeller[seller_id])'
            Format = '#,0'
            Folder = 'Commercial'
        },
        @{
            Name = 'Seller Orders'
            Expression = 'DISTINCTCOUNT(FactOrderSeller[order_id])'
            Format = '#,0'
            Folder = 'Seller Performance'
        },
        @{
            Name = 'Orders per Seller'
            Expression = 'DIVIDE([Seller Orders], [Active Sellers])'
            Format = '0.00'
            Folder = 'Commercial'
        },
        @{
            Name = 'Seller GMV'
            Expression = 'SUM(FactOrderSeller[product_value])'
            Format = '"R$" #,0.00'
            Folder = 'Seller Performance'
        },
        @{
            Name = 'Total Freight'
            Expression = 'SUM(FactOrders[freight_value])'
            Format = '"R$" #,0.00'
            Folder = 'Commercial'
        },
        @{
            Name = 'Freight-to-GMV Ratio'
            Expression = 'DIVIDE([Total Freight], [GMV])'
            Format = '0.00%'
            Folder = 'Commercial'
        },
        @{
            Name = 'Total Leads'
            Expression = 'SUM(FactAcquisition[total_leads])'
            Format = '#,0'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Won Leads'
            Expression = 'SUM(FactAcquisition[won_leads])'
            Format = '#,0'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Lead-to-Close Rate'
            Expression = 'DIVIDE([Won Leads], [Total Leads])'
            Format = '0.00%'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Activated Sellers'
            Expression = "CALCULATE(DISTINCTCOUNT(FactSellerLifecycle[seller_id]), FactSellerLifecycle[is_activated] = TRUE())"
            Format = '#,0'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Activation Rate'
            Expression = 'DIVIDE([Activated Sellers], [Won Leads])'
            Format = '0.00%'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Median Lead-to-Close Days'
            Expression = 'MEDIAN(FactSellerLifecycle[days_to_close])'
            Format = '0.00'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Median Days to First Sale'
            Expression = "MEDIANX(FILTER(FactSellerLifecycle, FactSellerLifecycle[is_activated] = TRUE()), FactSellerLifecycle[days_to_first_sale])"
            Format = '0.00'
            Folder = 'Acquisition'
        },
        @{
            Name = 'Delivered Orders'
            Expression = 'CALCULATE([Total Orders], FactOrders[delivery_status] IN {"on_time", "late"})'
            Format = '#,0'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'On-Time Orders'
            Expression = 'CALCULATE([Total Orders], FactOrders[delivery_status] = "on_time")'
            Format = '#,0'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'Late Orders'
            Expression = 'CALCULATE([Total Orders], FactOrders[delivery_status] = "late")'
            Format = '#,0'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'On-Time Delivery Rate'
            Expression = 'DIVIDE([On-Time Orders], [Delivered Orders])'
            Format = '0.00%'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'Late Delivery Rate'
            Expression = 'DIVIDE([Late Orders], [Delivered Orders])'
            Format = '0.00%'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'Average Delivery Days'
            Expression = 'AVERAGE(FactOrders[delivery_days])'
            Format = '0.00'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'Average Review Score'
            Expression = 'AVERAGEX(VALUES(FactOrderSeller[order_id]), CALCULATE(MAX(FactOrderSeller[average_review_score])))'
            Format = '0.00'
            Folder = 'Fulfilment and CX'
        },
        @{
            Name = 'Seller Delivered Orders'
            Expression = 'CALCULATE([Seller Orders], FactOrderSeller[delivery_status] IN {"on_time", "late"})'
            Format = '#,0'
            Folder = 'Seller Performance'
        },
        @{
            Name = 'Seller Late Orders'
            Expression = 'CALCULATE([Seller Orders], FactOrderSeller[delivery_status] = "late")'
            Format = '#,0'
            Folder = 'Seller Performance'
        },
        @{
            Name = 'Seller Late Delivery Rate'
            Expression = 'DIVIDE([Seller Late Orders], [Seller Delivered Orders])'
            Format = '0.00%'
            Folder = 'Seller Performance'
        }
    )

    foreach ($definition in $definitions) {
        $measureParameters = @{
            Table = $measureTable
            Name = $definition.Name
            Expression = $definition.Expression
            FormatString = $definition.Format
            DisplayFolder = $definition.Folder
        }
        Set-Measure @measureParameters
    }

    $placeholder = $measureTable.Columns |
        Where-Object Name -eq 'Placeholder'
    if ($placeholder) {
        $placeholder.IsHidden = $true
    }

    $model.SaveChanges()

    Write-Output "Database: $($database.Name)"
    Write-Output "Measures configured: $($definitions.Count)"
    Write-Output 'Tables:'
    $model.Tables |
        Where-Object { $_.Name -notmatch '^(LocalDateTable|DateTableTemplate)' } |
        Sort-Object Name |
        ForEach-Object { Write-Output "  $($_.Name)" }
} finally {
    if ($server.Connected) {
        $server.Disconnect()
    }
}
