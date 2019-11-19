<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" version="3.4.11-Madeira" styleCategories="Symbology|Labeling">
  <renderer-v2 type="graduatedSymbol" graduatedMethod="GraduatedColor" attr="IF (&quot;abfahrten&quot; = 0, NULL, &quot;abfahrten&quot;)" forceraster="0" symbollevels="0" enableorderby="0">
    <ranges>
      <range symbol="0" label=" ≤ 10 " lower="0.000000000000000" render="true" upper="10.000000000000000"/>
      <range symbol="1" label=" > 10 " lower="10.000000000000000" render="true" upper="20.000000000000000"/>
      <range symbol="2" label=" > 20 " lower="20.000000000000000" render="true" upper="40.000000000000000"/>
      <range symbol="3" label=" > 40 " lower="40.000000000000000" render="true" upper="60.000000000000000"/>
      <range symbol="4" label=" > 60 " lower="60.000000000000000" render="true" upper="80.000000000000000"/>
      <range symbol="5" label=" > 80 " lower="80.000000000000000" render="true" upper="100.000000000000000"/>
      <range symbol="6" label=" > 100 " lower="100.000000000000000" render="true" upper="125.000000000000000"/>
      <range symbol="7" label=" > 125 " lower="125.000000000000000" render="true" upper="150.000000000000000"/>
      <range symbol="8" label=" > 150 " lower="150.000000000000000" render="true" upper="175.000000000000000"/>
      <range symbol="9" label=" > 175 " lower="175.000000000000000" render="true" upper="200.000000000000000"/>
      <range symbol="10" label=" > 200 " lower="200.000000000000000" render="true" upper="250.000000000000000"/>
      <range symbol="11" label=" > 250 " lower="250.000000000000000" render="true" upper="300.000000000000000"/>
      <range symbol="12" label=" > 300 " lower="300.000000000000000" render="true" upper="350.000000000000000"/>
      <range symbol="13" label=" > 350 " lower="350.000000000000000" render="true" upper="400.000000000000000"/>
      <range symbol="14" label=" > 400 " lower="400.000000000000000" render="true" upper="999999999.000000000000000"/>
    </ranges>
    <symbols>
      <symbol alpha="1" type="marker" name="0" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="240,249,232,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="1" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="231,242,241,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="10" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="49,130,190,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="11" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="31,111,180,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="12" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="16,92,165,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="13" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="8,71,142,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="14" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="8,48,107,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="2" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="220,234,247,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="3" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="207,225,242,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="4" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="190,216,237,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="5" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="168,207,229,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="6" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="143,194,222,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="7" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="115,179,216,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="8" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="91,163,208,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
      <symbol alpha="1" type="marker" name="9" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="68,148,199,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <source-symbol>
      <symbol alpha="1" type="marker" name="0" force_rhr="0" clip_to_extent="1">
        <layer enabled="1" pass="0" locked="0" class="SimpleMarker">
          <prop v="0" k="angle"/>
          <prop v="247,251,255,255" k="color"/>
          <prop v="1" k="horizontal_anchor_point"/>
          <prop v="bevel" k="joinstyle"/>
          <prop v="circle" k="name"/>
          <prop v="0,0" k="offset"/>
          <prop v="3x:0,0,0,0,0,0" k="offset_map_unit_scale"/>
          <prop v="MM" k="offset_unit"/>
          <prop v="102,102,102,255" k="outline_color"/>
          <prop v="solid" k="outline_style"/>
          <prop v="0" k="outline_width"/>
          <prop v="3x:0,0,0,0,0,0" k="outline_width_map_unit_scale"/>
          <prop v="MM" k="outline_width_unit"/>
          <prop v="diameter" k="scale_method"/>
          <prop v="4" k="size"/>
          <prop v="3x:0,0,0,0,0,0" k="size_map_unit_scale"/>
          <prop v="MM" k="size_unit"/>
          <prop v="1" k="vertical_anchor_point"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" type="QString" name="name"/>
              <Option type="Map" name="properties">
                <Option type="Map" name="size">
                  <Option value="false" type="bool" name="active"/>
                  <Option value="2*(sqrt(&quot;abfahrten&quot;/pi()))" type="QString" name="expression"/>
                  <Option value="3" type="int" name="type"/>
                </Option>
              </Option>
              <Option value="collection" type="QString" name="type"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </source-symbol>
    <colorramp type="gradient" name="[source]">
      <prop v="240,249,232,255" k="color1"/>
      <prop v="8,48,107,255" k="color2"/>
      <prop v="0" k="discrete"/>
      <prop v="gradient" k="rampType"/>
      <prop v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255" k="stops"/>
    </colorramp>
    <mode name="equal"/>
    <symmetricMode enabled="false" symmetryPoint="45" astride="false"/>
    <rotation/>
    <sizescale/>
    <labelformat format=" > %1 " trimtrailingzeroes="false" decimalplaces="0"/>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style textColor="4,63,102,255" fontSizeMapUnitScale="3x:0,0,0,0,0,0" previewBkgrdColor="#ffffff" fontItalic="0" fontSize="10" fontStrikeout="0" fontSizeUnit="Point" fontCapitals="0" textOpacity="1" blendMode="0" useSubstitutions="0" multilineHeight="1" namedStyle="Standard" fontWeight="50" fontWordSpacing="0" isExpression="1" fieldName="IF (&quot;abfahrten&quot; > 0, &quot;name&quot; || '\\' || &quot;abfahrten&quot; || ' Abfahrten pro Werktag', NULL)" fontFamily="MS Shell Dlg 2" fontUnderline="0" fontLetterSpacing="0">
        <text-buffer bufferJoinStyle="128" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferSizeUnits="MM" bufferOpacity="1" bufferBlendMode="0" bufferDraw="1" bufferSize="0,6" bufferColor="255,255,255,255" bufferNoFill="1"/>
        <background shapeRotationType="0" shapeSVGFile="" shapeRadiiUnit="MM" shapeSizeType="0" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetX="0" shapeRadiiX="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRotation="0" shapeOpacity="1" shapeDraw="0" shapeRadiiY="0" shapeSizeY="0" shapeFillColor="255,255,255,255" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,255" shapeBlendMode="0" shapeSizeX="0" shapeType="0" shapeOffsetY="0" shapeOffsetUnit="MM" shapeSizeUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeBorderWidth="0" shapeJoinStyle="64"/>
        <shadow shadowUnder="0" shadowOpacity="0" shadowRadiusAlphaOnly="0" shadowOffsetUnit="MM" shadowOffsetAngle="135" shadowScale="100" shadowBlendMode="6" shadowOffsetDist="1" shadowRadius="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255" shadowOffsetGlobal="1" shadowRadiusUnit="MM" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowDraw="0"/>
        <substitutions/>
      </text-style>
      <text-format autoWrapLength="0" wrapChar="\" reverseDirectionSymbol="0" decimals="3" formatNumbers="0" multilineAlign="3" placeDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" addDirectionSymbol="0" rightDirectionSymbol=">" plussign="0" leftDirectionSymbol="&lt;"/>
      <placement distMapUnitScale="3x:0,0,0,0,0,0" placementFlags="10" fitInPolygonOnly="0" offsetUnits="MM" distUnits="MM" maxCurvedCharAngleIn="25" dist="0" placement="6" centroidWhole="0" repeatDistance="0" priority="5" xOffset="0" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" offsetType="1" preserveRotation="1" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" centroidInside="0" yOffset="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" repeatDistanceUnits="MM" rotationAngle="0" maxCurvedCharAngleOut="-25"/>
      <rendering mergeLines="0" fontLimitPixelSize="0" scaleMax="0" upsidedownLabels="0" scaleVisibility="0" obstacleType="0" fontMinPixelSize="3" minFeatureSize="0" obstacleFactor="1" zIndex="0" limitNumLabels="0" displayAll="0" fontMaxPixelSize="10000" maxNumLabels="2000" drawLabels="1" scaleMin="0" obstacle="1" labelPerPart="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" type="QString" name="name"/>
          <Option type="Map" name="properties">
            <Option type="Map" name="Color">
              <Option value="false" type="bool" name="active"/>
              <Option value="1" type="int" name="type"/>
              <Option value="" type="QString" name="val"/>
            </Option>
          </Option>
          <Option value="collection" type="QString" name="type"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>0</layerGeometryType>
</qgis>
