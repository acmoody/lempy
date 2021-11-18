# Lempy
Post-processing Python modules for the Lemhi MikeBasin model. The script contains a function for writing columns of timeseries data to individual dfs0 files for ingesting into the LRBM MikeBasin model and a function for reading MikeBasin model results into a temporary excel file. 

## Example Usage
### Writing data from excel file into dfs0s from the command line

```python
python lempy.py --mode w --workbook UpperLemhi_LRBM_InputTS_2015-v06.xlsm --datasheet WD74 --data_range B137:EX2788 --refrow 10 --refsheet Reference –outdir data
```

Argument list

--mode w  [Always for write mode]
--workbook [Excel workbook with data to send to dfs0s]
--datasheet [Sheet name holding data for dfs0s]
--data_range [Range of data to be exported including headers
--ref_sheet [Node name (col 1) and DHI ID (col 2) table]
--refrow [First row of node and ID data excluding any header lines]
--outdir [Defaults to ./data, location to write dfs0s]

### Read Mike results into excel via a temporary workbook. Outputs temporary workbook path

```python
python lempy.py --mode r --workbook CHCBM-FedDiv_All-32BIT-v03_test.xlsm --datasheet "BC1 Data" --header_range A47:BX52 --scenario_sheet Master --scenario_range A3:H8
```

Argument list

--mode r  [Always for read mode]
--workbook [Excel workbook to load results into]
--datasheet [Sheet name holding item data]
--header_range [Excel Range with data header holding Scenario, Arc Name, DHI Arc, Item Name, Load Data. Located in “datasheet”]
--scenario_sheet [Sheet holding table describing which scenarios to load]
--scenario_range [Cell range describing above table]

