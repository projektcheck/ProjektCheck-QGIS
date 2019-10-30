<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="Symbology|Labeling" version="3.4.11-Madeira" labelsEnabled="1">
  <renderer-v2 graduatedMethod="GraduatedColor" symbollevels="0" enableorderby="0" type="graduatedSymbol" forceraster="0" attr="IF (&quot;abfahrten&quot; = 0, NULL, &quot;abfahrten&quot;)">
    <ranges>
      <range upper="10.000000000000000" lower="0.000000000000000" symbol="0" label=" ≤ 10 " render="true"/>
      <range upper="20.000000000000000" lower="10.000000000000000" symbol="1" label=" > 10 " render="true"/>
      <range upper="40.000000000000000" lower="20.000000000000000" symbol="2" label=" > 20 " render="true"/>
      <range upper="60.000000000000000" lower="40.000000000000000" symbol="3" label=" > 40 " render="true"/>
      <range upper="80.000000000000000" lower="60.000000000000000" symbol="4" label=" > 60 " render="true"/>
      <range upper="100.000000000000000" lower="80.000000000000000" symbol="5" label=" > 80 " render="true"/>
      <range upper="125.000000000000000" lower="100.000000000000000" symbol="6" label=" > 100 " render="true"/>
      <range upper="150.000000000000000" lower="125.000000000000000" symbol="7" label=" > 125 " render="true"/>
      <range upper="175.000000000000000" lower="150.000000000000000" symbol="8" label=" > 150 " render="true"/>
      <range upper="200.000000000000000" lower="175.000000000000000" symbol="9" label=" > 175 " render="true"/>
      <range upper="250.000000000000000" lower="200.000000000000000" symbol="10" label=" > 200 " render="true"/>
      <range upper="300.000000000000000" lower="250.000000000000000" symbol="11" label=" > 250 " render="true"/>
      <range upper="350.000000000000000" lower="300.000000000000000" symbol="12" label=" > 300 " render="true"/>
      <range upper="400.000000000000000" lower="350.000000000000000" symbol="13" label=" > 350 " render="true"/>
      <range upper="999999999.000000000000000" lower="400.000000000000000" symbol="14" label=" > 400 " render="true"/>
    </ranges>
    <symbols>
      <symbol type="marker" alpha="1" clip_to_extent="1" name="0" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="1" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="10" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="11" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="12" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="13" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="14" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="2" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="3" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="4" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="5" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="6" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="7" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="8" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="9" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
      <symbol type="marker" alpha="1" clip_to_extent="1" name="0" force_rhr="0">
        <layer locked="0" enabled="1" pass="0" class="SimpleMarker">
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
    <symmetricMode astride="false" enabled="false" symmetryPoint="45"/>
    <rotation/>
    <sizescale/>
    <labelformat trimtrailingzeroes="false" decimalplaces="0" format=" > %1 "/>
  </renderer-v2>
  <labeling type="simple">
    <settings>
      <text-style textColor="4,63,102,255" fontWordSpacing="0" useSubstitutions="0" textOpacity="1" fontFamily="MS Shell Dlg 2" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontSize="10" previewBkgrdColor="#ffffff" fieldName="IF (&quot;abfahrten&quot; > 0, &quot;name&quot; || ' (' || &quot;abfahrten&quot; || ' Abfahrten pro Tag)', NULL)" fontUnderline="0" namedStyle="Standard" isExpression="1" fontCapitals="0" blendMode="0" fontItalic="0" fontLetterSpacing="0" multilineHeight="1" fontSizeUnit="Point" fontStrikeout="0" fontWeight="50">
        <text-buffer bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferJoinStyle="128" bufferBlendMode="0" bufferSize="0.9" bufferColor="255,255,255,255" bufferOpacity="1" bufferNoFill="1" bufferDraw="1"/>
        <background shapeType="0" shapeFillColor="255,255,255,255" shapeRotationType="0" shapeBorderWidth="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeSizeY="0" shapeRadiiY="0" shapeRadiiX="0" shapeSizeType="0" shapeBlendMode="0" shapeSVGFile="" shapeSizeX="0" shapeSizeUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeOpacity="1" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeOffsetUnit="MM" shapeRotation="0" shapeRadiiUnit="MM" shapeOffsetY="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeDraw="0" shapeOffsetX="0" shapeBorderColor="128,128,128,255" shapeBorderWidthUnit="MM"/>
        <shadow shadowOffsetGlobal="1" shadowDraw="0" shadowRadiusAlphaOnly="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowRadius="1.5" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255" shadowUnder="0" shadowScale="100" shadowOffsetDist="1" shadowOffsetUnit="MM" shadowRadiusUnit="MM" shadowBlendMode="6" shadowOffsetAngle="135" shadowOpacity="0.7"/>
        <substitutions/>
      </text-style>
      <text-format rightDirectionSymbol=">" wrapChar="" formatNumbers="0" reverseDirectionSymbol="0" useMaxLineLengthForAutoWrap="1" decimals="3" multilineAlign="3" placeDirectionSymbol="0" plussign="0" leftDirectionSymbol="&lt;" autoWrapLength="0" addDirectionSymbol="0"/>
      <placement centroidInside="0" centroidWhole="0" preserveRotation="1" distMapUnitScale="3x:0,0,0,0,0,0" distUnits="MM" xOffset="0" yOffset="0" offsetUnits="MM" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" rotationAngle="0" offsetType="1" maxCurvedCharAngleOut="-25" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" dist="0" priority="5" fitInPolygonOnly="0" placementFlags="10" quadOffset="4" repeatDistanceUnits="MM" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" maxCurvedCharAngleIn="25" placement="6" repeatDistance="0"/>
      <rendering obstacle="1" obstacleType="0" fontLimitPixelSize="0" scaleMin="0" fontMaxPixelSize="10000" scaleVisibility="0" limitNumLabels="0" minFeatureSize="0" labelPerPart="0" zIndex="0" scaleMax="0" displayAll="0" obstacleFactor="1" maxNumLabels="2000" upsidedownLabels="0" fontMinPixelSize="3" mergeLines="0" drawLabels="1"/>
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
