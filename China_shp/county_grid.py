import os
import shutil

import geopandas as gpd
import numpy as np
import rasterio
import xarray as xr
from rasterio.features import geometry_mask
from tqdm import tqdm

if __name__ == "__main__":
    gdf = gpd.read_file("./county_region_polygon_8656.shp")
    # 将gdf的geometry格式改为经纬度
    gdf.geometry = gdf.geometry.to_crs(epsg=4326)
    geometry = gdf.geometry.values # polygon
    cnty_code = gdf.CNTY_CODE.values # 城市代码

    # 新建一个分辨率为0.0001的数组
    interval=0.001
    x_range = np.arange(73.5, 135.5, interval)
    y_range = np.arange(54.0, 9.5 , -interval)
    x_size,y_size = interval,interval
    result_array = np.empty((len(y_range), len(x_range)), dtype=np.int32)
    result_array[:,:] = -999


    transform: rasterio.transform.Affine = rasterio.transform.from_origin(
        x_range[0], y_range[0], x_size, y_size
    )

    for (i_code,i_geo) in tqdm(zip(cnty_code, geometry),total=len(geometry)):
        mask: np.ndarray = geometry_mask(
                [i_geo],
                out_shape=(len(y_range), len(x_range)),
                transform=transform,
                invert=True,
            )
        result_array[mask] = i_code

    # 保存
    latitude = xr.DataArray(y_range, dims='latitude', coords={'latitude': y_range})
    longitude = xr.DataArray(x_range, dims='longitude', coords={'longitude': x_range})
    data_array = xr.DataArray(result_array, dims=('latitude', 'longitude'), coords={'latitude': latitude, 'longitude': longitude})
    ds = xr.Dataset({'code': data_array})
    if os.path.exists("china_code.zarr"):
        shutil.rmtree("china_code.zarr")
    ds.to_zarr("china_code.zarr")
