<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis labelsEnabled="1" styleCategories="Symbology|Labeling" version="3.10.6-A Coruña">
  <renderer-v2 forceraster="0" type="singleSymbol" enableorderby="0" symbollevels="0">
    <symbols>
      <symbol alpha="1" force_rhr="0" name="0" type="marker" clip_to_extent="1">
        <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
          <prop k="angle" v="0"/>
          <prop k="color" v="153,153,0,255"/>
          <prop k="horizontal_anchor_point" v="1"/>
          <prop k="joinstyle" v="bevel"/>
          <prop k="name" v="circle"/>
          <prop k="offset" v="0,0"/>
          <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="offset_unit" v="RenderMetersInMapUnits"/>
          <prop k="outline_color" v="77,77,77,255"/>
          <prop k="outline_style" v="solid"/>
          <prop k="outline_width" v="0"/>
          <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="outline_width_unit" v="RenderMetersInMapUnits"/>
          <prop k="scale_method" v="diameter"/>
          <prop k="size" v="2"/>
          <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
          <prop k="size_unit" v="RenderMetersInMapUnits"/>
          <prop k="vertical_anchor_point" v="1"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties" type="Map">
                <Option name="size" type="Map">
                  <Option value="true" name="active" type="bool"/>
                  <Option value="scale_linear( 2*(sqrt(&quot;abfahrten&quot;/pi())), 0,(2*(sqrt( maximum( &quot;abfahrten&quot;)/pi()))),3,40)" name="expression" type="QString"/>
                  <Option value="3" name="type" type="int"/>
                </Option>
              </Option>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
        </layer>
        <layer class="GeometryGenerator" locked="0" pass="0" enabled="1">
          <prop k="SymbolType" v="Marker"/>
          <prop k="geometryModifier" v="NULL"/>
          <data_defined_properties>
            <Option type="Map">
              <Option value="" name="name" type="QString"/>
              <Option name="properties"/>
              <Option value="collection" name="type" type="QString"/>
            </Option>
          </data_defined_properties>
          <symbol alpha="1" force_rhr="0" name="@0@1" type="marker" clip_to_extent="1">
            <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
              <prop k="angle" v="0"/>
              <prop k="color" v="153,153,0,255"/>
              <prop k="horizontal_anchor_point" v="1"/>
              <prop k="joinstyle" v="bevel"/>
              <prop k="name" v="circle"/>
              <prop k="offset" v="0,0"/>
              <prop k="offset_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="offset_unit" v="MM"/>
              <prop k="outline_color" v="77,77,77,255"/>
              <prop k="outline_style" v="solid"/>
              <prop k="outline_width" v="0"/>
              <prop k="outline_width_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="outline_width_unit" v="MM"/>
              <prop k="scale_method" v="diameter"/>
              <prop k="size" v="4"/>
              <prop k="size_map_unit_scale" v="3x:0,0,0,0,0,0"/>
              <prop k="size_unit" v="MM"/>
              <prop k="vertical_anchor_point" v="1"/>
              <data_defined_properties>
                <Option type="Map">
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style textOrientation="horizontal" fontSizeMapUnitScale="3x:0,0,0,0,0,0" fontWordSpacing="0" previewBkgrdColor="255,255,255,255" textOpacity="1" fontKerning="1" fontCapitals="0" fontUnderline="0" fontItalic="0" fontSizeUnit="Point" fontStrikeout="0" textColor="77,77,0,255" fontLetterSpacing="0" blendMode="0" fontFamily="MS Shell Dlg 2" fontSize="10" isExpression="1" useSubstitutions="0" multilineHeight="1" fieldName="IF (&quot;abfahrten&quot; > 0, &quot;name&quot; || '\\' || &quot;abfahrten&quot; || ' Abfahrten pro Werkag', NULL)" namedStyle="Standard" fontWeight="50">
        <text-buffer bufferNoFill="1" bufferBlendMode="0" bufferSizeUnits="MM" bufferSizeMapUnitScale="3x:0,0,0,0,0,0" bufferOpacity="1" bufferJoinStyle="128" bufferDraw="1" bufferSize="0" bufferColor="255,255,255,255"/>
        <background shapeOffsetMapUnitScale="3x:0,0,0,0,0,0" shapeRotationType="0" shapeSizeY="0" shapeRadiiX="0" shapeRadiiUnit="MM" shapeRadiiMapUnitScale="3x:0,0,0,0,0,0" shapeBorderColor="128,128,128,255" shapeBlendMode="0" shapeSizeX="0" shapeBorderWidthMapUnitScale="3x:0,0,0,0,0,0" shapeType="0" shapeSizeType="0" shapeOffsetX="0" shapeSizeUnit="MM" shapeFillColor="255,255,255,255" shapeOpacity="1" shapeRadiiY="0" shapeJoinStyle="64" shapeSVGFile="" shapeBorderWidth="0" shapeRotation="0" shapeBorderWidthUnit="MM" shapeDraw="0" shapeOffsetY="0" shapeOffsetUnit="MM" shapeSizeMapUnitScale="3x:0,0,0,0,0,0">
          <symbol alpha="1" force_rhr="0" name="markerSymbol" type="marker" clip_to_extent="1">
            <layer class="SimpleMarker" locked="0" pass="0" enabled="1">
              <prop k="angle" v="0"/>
              <prop k="color" v="190,207,80,255"/>
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
                  <Option value="" name="name" type="QString"/>
                  <Option name="properties"/>
                  <Option value="collection" name="type" type="QString"/>
                </Option>
              </data_defined_properties>
            </layer>
          </symbol>
        </background>
        <shadow shadowOffsetAngle="135" shadowRadius="0" shadowRadiusAlphaOnly="0" shadowOffsetDist="1" shadowOffsetUnit="MM" shadowRadiusUnit="MM" shadowOffsetMapUnitScale="3x:0,0,0,0,0,0" shadowScale="100" shadowBlendMode="6" shadowOpacity="0" shadowOffsetGlobal="1" shadowDraw="0" shadowRadiusMapUnitScale="3x:0,0,0,0,0,0" shadowColor="0,0,0,255" shadowUnder="0"/>
        <dd_properties>
          <Option type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
        </dd_properties>
        <substitutions/>
      </text-style>
      <text-format wrapChar="\" multilineAlign="3" addDirectionSymbol="0" placeDirectionSymbol="0" formatNumbers="0" rightDirectionSymbol=">" decimals="3" useMaxLineLengthForAutoWrap="1" autoWrapLength="0" plussign="0" reverseDirectionSymbol="0" leftDirectionSymbol="&lt;"/>
      <placement centroidInside="0" yOffset="0" priority="5" fitInPolygonOnly="0" overrunDistanceMapUnitScale="3x:0,0,0,0,0,0" preserveRotation="1" placement="6" maxCurvedCharAngleOut="-25" layerType="PointGeometry" quadOffset="4" offsetType="1" maxCurvedCharAngleIn="25" predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR" repeatDistanceUnits="MM" overrunDistanceUnit="MM" centroidWhole="0" rotationAngle="0" overrunDistance="0" repeatDistance="0" placementFlags="10" distMapUnitScale="3x:0,0,0,0,0,0" repeatDistanceMapUnitScale="3x:0,0,0,0,0,0" dist="0" labelOffsetMapUnitScale="3x:0,0,0,0,0,0" geometryGeneratorType="PointGeometry" geometryGeneratorEnabled="0" geometryGenerator="" distUnits="MM" xOffset="0" offsetUnits="MM"/>
      <rendering obstacle="1" limitNumLabels="0" upsidedownLabels="0" fontMaxPixelSize="10000" maxNumLabels="2000" scaleVisibility="0" mergeLines="0" zIndex="0" scaleMin="0" fontMinPixelSize="3" displayAll="0" scaleMax="0" minFeatureSize="0" labelPerPart="0" obstacleType="0" obstacleFactor="1" drawLabels="1" fontLimitPixelSize="0"/>
      <dd_properties>
        <Option type="Map">
          <Option value="" name="name" type="QString"/>
          <Option name="properties" type="Map">
            <Option name="BufferSize" type="Map">
              <Option value="true" name="active" type="bool"/>
              <Option value="0.8" name="expression" type="QString"/>
              <Option value="3" name="type" type="int"/>
            </Option>
          </Option>
          <Option value="collection" name="type" type="QString"/>
        </Option>
      </dd_properties>
      <callout type="simple">
        <Option type="Map">
          <Option value="pole_of_inaccessibility" name="anchorPoint" type="QString"/>
          <Option name="ddProperties" type="Map">
            <Option value="" name="name" type="QString"/>
            <Option name="properties"/>
            <Option value="collection" name="type" type="QString"/>
          </Option>
          <Option value="false" name="drawToAllParts" type="bool"/>
          <Option value="0" name="enabled" type="QString"/>
          <Option value="&lt;symbol alpha=&quot;1&quot; force_rhr=&quot;0&quot; name=&quot;symbol&quot; type=&quot;line&quot; clip_to_extent=&quot;1&quot;>&lt;layer class=&quot;SimpleLine&quot; locked=&quot;0&quot; pass=&quot;0&quot; enabled=&quot;1&quot;>&lt;prop k=&quot;capstyle&quot; v=&quot;square&quot;/>&lt;prop k=&quot;customdash&quot; v=&quot;5;2&quot;/>&lt;prop k=&quot;customdash_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;customdash_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;draw_inside_polygon&quot; v=&quot;0&quot;/>&lt;prop k=&quot;joinstyle&quot; v=&quot;bevel&quot;/>&lt;prop k=&quot;line_color&quot; v=&quot;60,60,60,255&quot;/>&lt;prop k=&quot;line_style&quot; v=&quot;solid&quot;/>&lt;prop k=&quot;line_width&quot; v=&quot;0.3&quot;/>&lt;prop k=&quot;line_width_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;offset&quot; v=&quot;0&quot;/>&lt;prop k=&quot;offset_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;prop k=&quot;offset_unit&quot; v=&quot;MM&quot;/>&lt;prop k=&quot;ring_filter&quot; v=&quot;0&quot;/>&lt;prop k=&quot;use_custom_dash&quot; v=&quot;0&quot;/>&lt;prop k=&quot;width_map_unit_scale&quot; v=&quot;3x:0,0,0,0,0,0&quot;/>&lt;data_defined_properties>&lt;Option type=&quot;Map&quot;>&lt;Option value=&quot;&quot; name=&quot;name&quot; type=&quot;QString&quot;/>&lt;Option name=&quot;properties&quot;/>&lt;Option value=&quot;collection&quot; name=&quot;type&quot; type=&quot;QString&quot;/>&lt;/Option>&lt;/data_defined_properties>&lt;/layer>&lt;/symbol>" name="lineSymbol" type="QString"/>
          <Option value="0" name="minLength" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="minLengthMapUnitScale" type="QString"/>
          <Option value="MM" name="minLengthUnit" type="QString"/>
          <Option value="0" name="offsetFromAnchor" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromAnchorMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromAnchorUnit" type="QString"/>
          <Option value="0" name="offsetFromLabel" type="double"/>
          <Option value="3x:0,0,0,0,0,0" name="offsetFromLabelMapUnitScale" type="QString"/>
          <Option value="MM" name="offsetFromLabelUnit" type="QString"/>
        </Option>
      </callout>
    </settings>
  </labeling>
  <blendMode>0</blendMode>
  <featureBlendMode>0</featureBlendMode>
  <layerGeometryType>0</layerGeometryType>
</qgis>
