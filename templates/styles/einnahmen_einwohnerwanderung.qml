<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.10.3-A Coruña" labelsEnabled="1" styleCategories="Symbology|Labeling">
  <renderer-v2 type="singleSymbol" forceraster="0" enableorderby="0" symbollevels="0">
    <symbols>
      <symbol type="fill" name="0" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer enabled="1" pass="0" class="SimpleFill" locked="0">
          <prop k="border_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="color" v="35,139,69,255"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="MM"/>
          <prop k="outline_color" v="76,76,76,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0.2"/>
          <prop k="outline_width_unit" v="MM"/>
          <prop k="style" v="solid"/>
          <data_defined_properties>
            <Option type="Map">
              <Option type="QString" name="name" value=""/>
              <Option type="Map" name="properties">
                <Option type="Map" name="fillColor">
                  <Option type="bool" name="active" value="true"/>
                  <Option type="QString" name="expression" value="coalesce(ramp_color(create_ramp(map(0,'#67000d',0.13,'#a50f15',0.26,'#cb181d',0.39,'#ef3b2c',0.52,'#fb6a4a',0.65,'#fc9272',0.78,'#fcbba1',0.9,'#fee0d2',1,'#fff5f0')),scale_linear(IF (&quot;saldo&quot; > 0, NULL, &quot;saldo&quot;), minimum(&quot;saldo&quot;), 0, 0, 1)), '#238b45')"/>
                  <Option type="int" name="type" value="3"/>
                </Option>
              </Option>
              <Option type="QString" name="type" value="collection"/>
            </Option>
          </data_defined_properties>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fontKerning="1" fontSizeUnit="Point" fontItalic="0" fontCapitals="0" previewBkgrdColor="255,255,255,255" fontStrikeout="0" isExpression="1" blendMode="0" fontWeight="50" fieldName=" round( &quot;saldo&quot;, 1)" fontSize="8" fontLetterSpacing="0" useSubstitutions="0" fontUnderline="0" namedStyle="Standard" textOrientation="horizontal" fontWordSpacing="0" textOpacity="1" fontSizeMapUnitScale="3x:0,0,0,0,0,0" textColor="0,0,0,255" fontFamily="MS Shell Dlg 2" multilineHeight="1">
        <text-buffer bufferSizeUnits="MM" bufferDraw="1" bufferJoinStyle="128" bufferBlendMode="0" bufferSize="0" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferColor="255,255,255,255" bufferOpacity="1" bufferNoFill="1"/>
        <background shapeBorderWidth="0" shapeBlendMode="0" shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeSizeType="0" shapeSizeX="0" shapeRotationType="0" shapeBorderColor="128,128,128,255" shapeDraw="0" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeJoinStyle="64" shapeRadiiX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeBorderWidthUnit="MM" shapeOpacity="1" shapeFillColor="255,255,255,255" shapeSizeY="0" shapeOffsetX="0" shapeSizeUnit="MM" shapeRotation="0" shapeRadiiY="0" shapeRadiiUnit="MM" shapeOffsetY="0" shapeOffsetUnit="MM" shapeSVGFile="" shapeSizeMapUnitScale="3x:0,0,0,0,0,0" shapeType="0">
          <symbol type="marker" name="markerSymbol" alpha="1" clip_to_extent="1" force_rhr="0">
            <layer enabled="1" pass="0" class="SimpleMarker" locked="0">
              <prop k="angle" v="0"/>
              <prop k="color" v="243,166,178,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="35,35,35,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="2"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option type="QString" name="name" value=""/>
                  <Option name="properties"/>
                  <Option type="QString" name="type" value="collection"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowRadiusUnit="MM" shadowRadiusAlphaOnly="0" shadowRadius="0" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowOpacity="0" shadowScale="100" shadowColor="0,0,0,255" shadowBlendMode="6" shadowOffsetDist="1" shadowDraw="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowUnder="0" shadowOffsetUnit="MM" shadowOffsetAngle="135" shadowOffsetGlobal="1"/>
        <dd_properties>
          <Option type="Map">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format placeDirectionSymbol="0" decimals="3" multilineAlign="0" useMaxLineLengthForAutoWrap="1" leftDirectionSymbol="&lt;" autoWrapLength="0" reverseDirectionSymbol="0" plussign="0" rightDirectionSymbol=">" wrapChar="" addDirectionSymbol="0" formatNumbers="0"/>
      <placement layerType="PolygonGeometry" placement="1" xOffset="0" offsetType="0" distUnits="MM" dist="0" placementFlags="10" geometryGenerator="" overrunDistance="0" centroidInside="0" repeatDistanceUnits="MM" fitInPolygonOnly="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" distMapUnitScale="3x:0,0,0,0,0,0" offsetUnits="MM" priority="5" yOffset="0" maxCurvedCharAngleOut="-25" geometryGeneratorType="PointGeometry" centroidWhole="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" quadOffset="4" maxCurvedCharAngleIn="25" rotationAngle="0" overrunDistanceUnit="MM" preserveRotation="1" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" geometryGeneratorEnabled="0" repeatDistance="0"/>
      <rendering fontMaxPixelSize="10000" obstacleType="0" scaleMin="0" obstacleFactor="1" upsidedownLabels="0" scaleMax="0" mergeLines="0" fontLimitPixelSize="0" fontMinPixelSize="3" obstacle="1" zIndex="0" limitNumLabels="0" scaleVisibility="0" drawLabels="1" displayAll="0" maxNumLabels="2000" minFeatureSize="0" labelPerPart="0"/>
      <dd_properties>
        <Option type="Map">
          <Option type="QString" name="name" value=""/>
          <Option type="Map" name="properties">
            <Option type="Map" name="BufferSize">
              <Option type="bool" name="active" value="true"/>
              <Option type="QString" name="expression" value="0.75"/>
              <Option type="int" name="type" value="3"/>
            </Option>
          </Option>
          <Option type="QString" name="type" value="collection"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option type="QString" name="anchorPoint" value="pole_of_inaccessibility"/>
          <Option type="Map" name="ddProperties">
            <Option type="QString" name="name" value=""/>
            <Option name="properties"/>
            <Option type="QString" name="type" value="collection"/>
          </Option>
          <Option type="bool" name="drawToAllParts" value="false"/>
          <Option type="QString" name="enabled" value="0"/>
          <Option type="QString" name="lineSymbol" value="&lt;symbol type=&quot;line&quot; name=&quot;symbol&quot; alpha=&quot;1&quot; clip_to_extent=&quot;1&quot; force_rhr=&quot;0&quot;>&lt;layer enabled=&quot;1&quot; pass=&quot;0&quot; class=&quot;SimpleLine&quot; locked=&quot;0&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option type=&quot;QString&quot; name=&quot;name&quot; value=&quot;&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option type=&quot;QString&quot; name=&quot;type&quot; value=&quot;collection&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>"/>
          <Option type="double" name="minLength" value="0"/>
          <Option type="QString" name="minLengthMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="minLengthUnit" value="MM"/>
          <Option type="double" name="offsetFromAnchor" value="0"/>
          <Option type="QString" name="offsetFromAnchorMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromAnchorUnit" value="MM"/>
          <Option type="double" name="offsetFromLabel" value="0"/>
          <Option type="QString" name="offsetFromLabelMapUnitScale" value="3x:0,0,0,0,0,0"/>
          <Option type="QString" name="offsetFromLabelUnit" value="MM"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>2</layerGeometryType>
</qgis>
